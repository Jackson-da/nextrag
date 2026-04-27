"""请求日志中间件 - 支持 trace_id 追踪"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 企业级标准"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成 trace_id（优先使用请求头中的）
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        
        # 获取带 trace_id 的日志器
        log = get_logger(trace_id=trace_id)
        
        # 记录请求开始
        start_time = time.time()
        log.info(
            "请求开始",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_type=request.headers.get("content-type"),
        )

        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算耗时
            duration = time.time() - start_time
            
            # 记录请求结束
            log.info(
                "请求完成",
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
            )
            
            # 在响应头中添加 trace_id，方便客户端排查
            response.headers["X-Trace-ID"] = trace_id
            
            return response

        except Exception as e:
            duration = time.time() - start_time
            log.error(
                "请求异常",
                error=str(e),
                error_type=type(e).__name__,
                duration=f"{duration:.3f}s",
            )
            raise
