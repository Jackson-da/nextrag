"""聊天 API 接口"""
from typing import Annotated, AsyncIterator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
)
from app.services.chat_service import get_chat_service

router = APIRouter(prefix="/chat", tags=["问答"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """非流式问答"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    chat_service = get_chat_service()
    
    try:
        result = await chat_service.chat(
            question=request.question,
            session_id=request.session_id,
            stream=False,
        )
        
        return ChatResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            sources=result.get("sources", []),
            latency=result.get("latency", 0),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答服务出错: {str(e)}")


async def generate_sse_events(
    chat_service,
    question: str,
    session_id: str,
) -> AsyncIterator[dict]:
    """生成 SSE 事件流"""
    try:
        async for event in chat_service.stream_chat(
            question=question,
            session_id=session_id,
        ):
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False)
            }
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}, ensure_ascii=False)
        }


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """流式问答（Server-Sent Events）"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    chat_service = get_chat_service()
    
    return EventSourceResponse(
        generate_sse_events(
            chat_service=chat_service,
            question=request.question,
            session_id=request.session_id,
        )
    )


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清除对话历史"""
    chat_service = get_chat_service()
    success = chat_service.clear_history(session_id)
    
    return {"success": success, "message": "对话历史已清除"}


@router.get("/history/{session_id}")
async def get_history(session_id: str):
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
async def chat_health_check():
    """问答服务健康检查"""
    chat_service = get_chat_service()
    is_healthy = await chat_service.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "llm_connected": is_healthy,
    }
