"""系统 API 接口"""
from fastapi import APIRouter

router = APIRouter(tags=["系统"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    from app.services.document_service import get_document_service
    from app.services.chat_service import get_chat_service
    from app import __version__
    
    try:
        doc_service = get_document_service()
        vectorstore_info = await doc_service.get_vectorstore_info()
        chat_service = get_chat_service()
        llm_connected = await chat_service.health_check()
        
        return {
            "status": "healthy",
            "version": __version__,
            "llm_connected": llm_connected,
            "vectorstore_connected": True,
            "document_count": vectorstore_info.get("count", 0),
        }
    except Exception as e:
        return {
            "status": "degraded",
            "version": __version__,
            "llm_connected": False,
            "vectorstore_connected": False,
            "document_count": 0,
            "error": str(e),
        }
