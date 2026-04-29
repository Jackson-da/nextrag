"""聊天 API 接口"""
import json
import structlog
import uuid
from collections.abc import AsyncIterator
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
)
from app.models.user import UserModel
from app.services.chat_service import get_chat_service
from app.api.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["问答"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """非流式问答
    
    Args:
        request: 包含 question, session_id, knowledge_base_id(可选)
        current_user: 当前登录用户
    """
    # 生成请求追踪 ID
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(
        "收到问答请求",
        request_id=request_id,
        user_id=current_user.id,
        session_id=request.session_id,
        kb_id=request.knowledge_base_id,
        kb_filtered=request.knowledge_base_id is not None,
        question_length=len(request.question),
    )
    
    chat_service = get_chat_service()
    
    try:
        result = await chat_service.chat(
            question=request.question,
            session_id=request.session_id,
            stream=False,
            kb_id=request.knowledge_base_id,
            user_id=current_user.id,
        )
        
        logger.info(
            "问答请求完成",
            request_id=request_id,
            session_id=request.session_id,
            latency=result.get("latency", 0),
            sources_count=len(result.get("sources", [])),
        )
        
        return ChatResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            sources=result.get("sources", []),
            latency=result.get("latency", 0),
        )
    
    except Exception as e:
        logger.error(
            "问答请求失败",
            request_id=request_id,
            session_id=request.session_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"问答服务出错: {str(e)}")


async def generate_sse_events(
    chat_service,
    question: str,
    session_id: str,
    kb_id: str | None,
    user_id: str | None,
    request_id: str = "",
) -> AsyncIterator[dict]:
    """生成 SSE 事件流
    
    Args:
        chat_service: 聊天服务实例
        question: 用户问题
        session_id: 会话 ID
        kb_id: 知识库 ID
        user_id: 用户 ID
        request_id: 请求追踪 ID
    """
    try:
        async for event in chat_service.stream_chat(
            question=question,
            session_id=session_id,
            kb_id=kb_id,
            user_id=user_id,
        ):
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False)
            }
        
        logger.info(
            "流式问答完成",
            request_id=request_id,
            session_id=session_id,
        )
    except Exception as e:
        logger.error(
            "流式问答失败",
            request_id=request_id,
            session_id=session_id,
            error=str(e),
        )
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}, ensure_ascii=False)
        }


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """流式问答（Server-Sent Events）
    
    Args:
        request: 包含 question, session_id, knowledge_base_id(可选)
        current_user: 当前登录用户
    """
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(
        "收到流式问答请求",
        request_id=request_id,
        user_id=current_user.id,
        session_id=request.session_id,
        kb_id=request.knowledge_base_id,
        kb_filtered=request.knowledge_base_id is not None,
        question_length=len(request.question),
    )
    
    chat_service = get_chat_service()
    
    return EventSourceResponse(
        generate_sse_events(
            chat_service=chat_service,
            question=request.question,
            session_id=request.session_id,
            kb_id=request.knowledge_base_id,
            user_id=current_user.id,
            request_id=request_id,
        )
    )


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """清除对话历史"""
    chat_service = get_chat_service()
    success = chat_service.clear_history(session_id)
    
    return {"success": success, "message": "对话历史已清除"}


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取对话历史"""
    chat_service = get_chat_service()
    history = chat_service.get_history(session_id)
    
    return {
        "session_id": session_id,
        "messages": [
            {"role": msg.type, "content": msg.content}
            for msg in history
        ]
    }


@router.post("/health")
async def chat_health_check(
    current_user: UserModel = Depends(get_current_user),
):
    """问答服务健康检查"""
    chat_service = get_chat_service()
    health_result = await chat_service.health_check()
    
    llm_connected = health_result.get("llm", False)
    redis_connected = health_result.get("redis", False)
    
    return {
        "status": "healthy" if llm_connected else "unhealthy",
        "llm_connected": llm_connected,
        "redis_connected": redis_connected,
    }
