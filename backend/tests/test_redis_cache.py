"""Redis 连接测试（同步版本）"""
import pytest
import json
from redis import Redis


class TestRedisConnection:
    """Redis 连接测试"""

    @pytest.fixture
    def redis_client(self):
        """创建 Redis 客户端"""
        try:
            client = Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            client.ping()
            yield client
            client.close()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    def test_redis_ping(self, redis_client):
        """测试 Redis 连接"""
        result = redis_client.ping()
        assert result is True

    def test_set_get_delete(self, redis_client):
        """测试基本 SET/GET/DELETE 操作"""
        key = "test:basic:key"
        value = "Hello Redis!"
        
        # SET
        redis_client.set(key, value)
        
        # GET
        result = redis_client.get(key)
        assert result == value
        
        # DELETE
        redis_client.delete(key)
        result = redis_client.get(key)
        assert result is None

    def test_setex_with_ttl(self, redis_client):
        """测试带过期时间的 SETEX"""
        key = "test:ttl:key"
        value = "value"
        
        redis_client.setex(key, 60, value)
        ttl = redis_client.ttl(key)
        
        assert 0 < ttl <= 60
        redis_client.delete(key)

    def test_message_cache_scenario(self, redis_client):
        """测试消息缓存场景"""
        session_id = "test-session-123"
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你？"}
        ]
        
        # 写入缓存
        cache_key = f"chat:messages:{session_id}"
        redis_client.setex(cache_key, 1800, json.dumps(messages))
        
        # 读取缓存
        cached = redis_client.get(cache_key)
        parsed = json.loads(cached)
        assert len(parsed) == 2
        assert parsed[0]["role"] == "user"
        
        # 清理
        redis_client.delete(cache_key)


class TestLLMResponseCache:
    """LLM 回答缓存集成测试（需要真实 Redis）"""

    @pytest.fixture
    def redis_client(self):
        """创建 Redis 客户端"""
        try:
            client = Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            client.ping()
            yield client
            client.close()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    def test_llm_cache_miss_then_hit(self, redis_client):
        """测试 LLM 缓存 MISS -> HIT 流程"""
        import hashlib
        from app.core.cache import CacheKeys
        
        question = "今天天气怎么样"
        question_hash = hashlib.md5(question.encode()).hexdigest()
        cache_key = CacheKeys.llm_response(question_hash)
        
        # 清理可能存在的旧缓存
        redis_client.delete(cache_key)
        
        # 第一次访问：MISS
        cached = redis_client.get(cache_key)
        assert cached is None
        
        # 计算回答（模拟）
        answer = "今天天气晴朗，适合出行"
        
        # 写入缓存
        cache_data = {
            "answer": answer,
            "sources": [{"content": "天气预报"}]
        }
        redis_client.setex(cache_key, CacheKeys.TTL_META, json.dumps(cache_data))
        
        # 第二次访问：HIT
        cached = redis_client.get(cache_key)
        assert cached is not None
        
        parsed = json.loads(cached)
        assert parsed["answer"] == answer
        
        # 清理
        redis_client.delete(cache_key)

    def test_different_questions_independent_cache(self, redis_client):
        """测试不同问题有独立缓存"""
        import hashlib
        from app.core.cache import CacheKeys
        
        q1 = "问题1"
        q2 = "问题2"
        
        key1 = CacheKeys.llm_response(hashlib.md5(q1.encode()).hexdigest())
        key2 = CacheKeys.llm_response(hashlib.md5(q2.encode()).hexdigest())
        
        # 清理可能存在的旧缓存
        redis_client.delete(key1)
        redis_client.delete(key2)
        
        redis_client.setex(key1, 3600, json.dumps({"answer": "回答1", "sources": []}))
        redis_client.setex(key2, 3600, json.dumps({"answer": "回答2", "sources": []}))
        
        # 验证两个缓存独立
        result1 = json.loads(redis_client.get(key1))
        result2 = json.loads(redis_client.get(key2))
        
        assert result1["answer"] == "回答1"
        assert result2["answer"] == "回答2"
        
        # 清理
        redis_client.delete(key1)
        redis_client.delete(key2)

    def test_chinese_question_caching(self, redis_client):
        """测试中文问题缓存"""
        import hashlib
        from app.core.cache import CacheKeys
        
        chinese_question = "你们公司的产品有哪些"
        question_hash = hashlib.md5(chinese_question.encode()).hexdigest()
        cache_key = CacheKeys.llm_response(question_hash)
        
        # 清理可能存在的旧缓存
        redis_client.delete(cache_key)
        
        cached_data = {
            "answer": "我们公司有以下产品...",
            "sources": [{"content": "产品介绍文档"}]
        }
        
        redis_client.setex(cache_key, 3600, json.dumps(cached_data, ensure_ascii=False))
        
        result = json.loads(redis_client.get(cache_key))
        assert result["answer"] == "我们公司有以下产品..."
        assert len(result["sources"]) == 1
        
        # 清理
        redis_client.delete(cache_key)
