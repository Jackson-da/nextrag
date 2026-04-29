"""Redis 缓存模块"""
import json
from typing import Any, Callable, TypeVar
import structlog
from redis.asyncio import Redis, ConnectionPool

from app.config import get_settings

logger = structlog.get_logger()

_redis: Redis | None = None
_redis_available: bool | None = None
T = TypeVar("T")


async def get_redis() -> Redis | None:
    """获取 Redis 连接（可能为 None）"""
    global _redis, _redis_available
    
    settings = get_settings()
    
    # 检查是否启用
    if not settings.redis_enabled:
        if _redis_available is None:
            logger.info("Redis 缓存已禁用")
            _redis_available = False
        return None
    
    # 单例模式
    if _redis is None:
        try:
            pool = ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=settings.redis_max_connections,
            )
            _redis = Redis(connection_pool=pool)
            
            # 测试连接
            await _redis.ping()
            _redis_available = True
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用降级方案: {e}")
            _redis_available = False
            _redis = None
    
    return _redis


async def close_redis():
    """关闭 Redis 连接"""
    global _redis, _redis_available
    if _redis:
        await _redis.close()
        _redis = None
        _redis_available = None


def is_redis_available() -> bool:
    """检查 Redis 是否可用"""
    return _redis_available is True


async def get_or_set(
    key: str,
    fetch_func: Callable[..., Any],
    ttl: int = 1800,
    *args,
    **kwargs
) -> Any:
    """获取缓存，未命中时执行 fetch_func 并缓存
    
    Args:
        key: 缓存键
        fetch_func: 缓存未命中时的回调函数
        ttl: 过期时间（秒）
        *args, **kwargs: 传递给 fetch_func 的参数
    
    Returns:
        缓存数据或 fetch_func 的返回值
    """
    redis = await get_redis()
    
    # Redis 可用时尝试获取缓存
    if redis:
        try:
            data = await redis.get(key)
            if data:
                logger.debug(f"缓存命中: {key}")
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis 读取失败: {e}")
    
    # 未命中或 Redis 不可用，执行回调
    result = fetch_func(*args, **kwargs)
    
    # 如果是协程，需要 await
    import asyncio
    if asyncio.iscoroutine(result):
        result = await result
    
    # 回填缓存
    if redis and result is not None:
        try:
            await redis.setex(key, ttl, json.dumps(result, default=str))
            logger.debug(f"缓存写入: {key}")
        except Exception as e:
            logger.warning(f"Redis 写入失败: {e}")
    
    return result


async def delete_cache(*keys: str) -> bool:
    """删除缓存
    
    Args:
        *keys: 要删除的缓存键
    
    Returns:
        是否成功（即使 Redis 不可用也返回 True）
    """
    redis = await get_redis()
    
    if not redis:
        return True
    
    try:
        for key in keys:
            await redis.delete(key)
            logger.debug(f"缓存删除: {key}")
        return True
    except Exception as e:
        logger.warning(f"Redis 删除失败: {e}")
        return False


async def delete_cache_pattern(pattern: str) -> int:
    """删除匹配模式的所有缓存
    
    Args:
        pattern: 匹配模式，如 "chat:messages:*"
    
    Returns:
        删除的键数量
    """
    redis = await get_redis()
    
    if not redis:
        return 0
    
    try:
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            count = await redis.delete(*keys)
            logger.info(f"批量删除缓存: {pattern}, 数量: {count}")
            return count
        return 0
    except Exception as e:
        logger.warning(f"Redis 批量删除失败: {e}")
        return 0


# ============== 缓存 Key 工具 ==============

class CacheKeys:
    """缓存 Key 生成器"""
    
    # TTL 常量（秒）
    TTL_MESSAGES = 1800      # 30 分钟
    TTL_META = 3600          # 1 小时
    TTL_SESSIONS = 600       # 10 分钟
    
    @staticmethod
    def messages(session_id: str) -> str:
        """会话消息列表"""
        return f"chat:messages:{session_id}"
    
    @staticmethod
    def meta(session_id: str) -> str:
        """会话元信息"""
        return f"chat:meta:{session_id}"
    
    @staticmethod
    def sessions(user_id: str) -> str:
        """用户会话列表"""
        return f"chat:sessions:{user_id}"
