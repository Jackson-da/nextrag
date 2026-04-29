"""系统 API 接口"""
import structlog
from fastapi import APIRouter

from app import __version__
from app.models.schemas import HealthResponse

logger = structlog.get_logger()
router = APIRouter(tags=["系统"])


@router.get("/ping")
async def ping():
    """简单的存活探测（用于负载均衡器）"""
    return {"status": "ok", "version": __version__}


# 极简健康检查（不带前缀，用于负载均衡器/容器探测）
# 这个端点不带 /api/v1 前缀
simple_health_router = APIRouter(tags=["系统"])


@simple_health_router.get("/health")
async def simple_health():
    """极简存活探测，不涉及业务逻辑"""
    return {"status": "ok", "version": __version__}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点
    
    返回服务各组件的连接状态。
    """
    from app.services.document_service import get_document_service
    from app.services.chat_service import get_chat_service
    
    try:
        # 检查 LLM 连接
        chat_service = get_chat_service()
        health_result = await chat_service.health_check()
        llm_connected = health_result.get("llm", False)
    except Exception as e:
        logger.warning("LLM 健康检查失败", error=str(e))
        llm_connected = False
    
    try:
        # 检查向量库
        doc_service = get_document_service()
        vectorstore_info = await doc_service.get_vectorstore_info()
        vectorstore_connected = True
        document_count = vectorstore_info.get("count", 0)
    except Exception as e:
        logger.warning("向量库健康检查失败", error=str(e))
        vectorstore_connected = False
        document_count = 0
    
    # 判断整体状态
    if llm_connected and vectorstore_connected:
        status = "healthy"
    else:
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version=__version__,
        llm_connected=llm_connected,
        vectorstore_connected=vectorstore_connected,
        document_count=document_count,
    )



