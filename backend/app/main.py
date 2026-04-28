"""FastAPI 应用主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import structlog

from app.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.middleware.logging import LoggingMiddleware
from app.api import document_router, chat_router, chat_session_router, knowledge_router, system_router, simple_health_router, auth_router
from app import __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger = get_logger()
    logger.info("应用启动中...", version=__version__)

    # 启动时执行
    settings = get_settings()
    logger.info(
        "配置加载完成",
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        log_console=settings.log_console,
        log_file=settings.log_file,
    )

    yield

    # 关闭时执行 - 清理所有资源
    logger.info("应用关闭中...")
    
    try:
        # 清理全局服务实例
        from app.services import chat_service as chat_service_module
        from app.services import document_service as document_service_module
        
        # 重置文档服务（先关闭以释放向量库资源）
        if hasattr(document_service_module, '_document_service'):
            doc_service = document_service_module._document_service
            if doc_service is not None:
                doc_service.close()
            document_service_module._document_service = None
            logger.info("文档服务已清理")
        
        # 重置聊天服务
        if hasattr(chat_service_module, '_chat_service'):
            chat_service_module._chat_service = None
            logger.info("聊天服务已清理")
        
        # 清理依赖注入容器
        from app.core.container import reset_container
        reset_container()
        logger.info("依赖注入容器已重置")
        
        # 关闭数据库连接
        from app.models.database import close_db
        close_db()
        logger.info("数据库连接已关闭")
        
        logger.info("应用关闭完成")
    except Exception as e:
        logger.error("清理资源时出错", error=str(e))


# 创建 FastAPI 应用
settings = get_settings()

# 初始化日志
setup_logging(
    level=settings.log_level,
    console=settings.log_console,
    file=settings.log_file,
    file_path=settings.log_file_path,
    error_file=settings.log_error_file,
    file_max_bytes=settings.log_file_max_bytes,
    file_backup_count=settings.log_file_backup_count,
)

app = FastAPI(
    title="智能文档问答系统",
    description="基于 RAG 的企业级智能文档问答系统 API",
    version=__version__,
    lifespan=lifespan,
    docs_url=None,  # 禁用默认 docs，使用自定义路由
    redoc_url=None,
)

# 注册请求日志中间件
app.add_middleware(LoggingMiddleware)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 自定义 /docs 路由 - 使用国内 CDN (bootcdn)
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """自定义 API 文档页面，使用国内 CDN"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>智能文档问答系统 - API 文档</title>
        <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.0/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/openapi.json",
                    dom_id: "#swagger-ui",
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            };
        </script>
    </body>
    </html>
    """)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    try:
        logger = get_logger()
        logger.error(
            "请求处理异常",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
    except Exception:
        # 如果logger初始化失败，使用structlog的标准方式
        structlog.get_logger().error(
            "请求处理异常",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.log_level == "DEBUG" else None,
        }
    )


# 注册路由
app.include_router(simple_health_router)  # /health - 不带前缀
app.include_router(document_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(chat_session_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


# 根路由
@app.get("/", tags=["首页"])
async def root():
    """首页"""
    return {
        "name": "智能文档问答系统",
        "version": __version__,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.log_level == "DEBUG",
        log_level=settings.log_level.lower(),
    )
