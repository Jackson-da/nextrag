"""请求日志中间件"""
import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 获取日志器
        log = structlog.get_logger()

        # 记录请求开始
        start_time = time.time()
        log.info(
            "请求开始",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算耗时
            duration = time.time() - start_time

            # 记录请求结束
            log.info(
                "请求完成",
                request_id=request_id,
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            log.error(
                "请求异常",
                request_id=request_id,
                error=str(e),
                duration=f"{duration:.3f}s",
            )
            raise
