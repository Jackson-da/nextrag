"""API 接口层包"""
from app.api.document import router as document_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.api.system import router as system_router, simple_health_router

__all__ = [
    "document_router",
    "chat_router",
    "knowledge_router",
    "system_router",
]
