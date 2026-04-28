"""聊天会话管理 API"""
import uuid
from datetime import datetime
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.user import UserModel
from app.models.chat import ChatSessionModel, ChatMessageModel
from app.api.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter(prefix="/chat/sessions", tags=["会话管理"])


# ============== 请求/响应模型 ==============

class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    title: str | None = Field(default=None, max_length=200)
    knowledge_base_id: str | None = None


class SessionUpdateRequest(BaseModel):
    """更新会话请求"""
    title: str | None = Field(default=None, max_length=200)


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    user_id: str
    title: str
    knowledge_base_id: str | None
    message_count: int
    created_at: str | None
    updated_at: str | None


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse]


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    session_id: str
    role: str
    content: str
    sources: list | None
    created_at: str | None


class MessageListResponse(BaseModel):
    """消息列表响应"""
    session_id: str
    messages: list[MessageResponse]


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    message: str


# ============== API 路由 ==============

@router.get("", response_model=SessionListResponse)
async def list_sessions(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户所有会话列表"""
    sessions = (
        db.query(ChatSessionModel)
        .filter(ChatSessionModel.user_id == current_user.id)
        .order_by(ChatSessionModel.updated_at.desc())
        .all()
    )
    
    logger.info("获取会话列表", user_id=current_user.id, count=len(sessions))
    
    return SessionListResponse(
        sessions=[SessionResponse(**s.to_dict()) for s in sessions]
    )


@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest | None = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新会话"""
    session_id = str(uuid.uuid4())
    title = request.title if request and request.title else "新对话"
    kb_id = request.knowledge_base_id if request else None
    
    session = ChatSessionModel(
        id=session_id,
        user_id=current_user.id,
        title=title,
        knowledge_base_id=kb_id,
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    logger.info("创建会话", user_id=current_user.id, session_id=session_id)
    
    return SessionResponse(**session.to_dict())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话详情"""
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return SessionResponse(**session.to_dict())


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新会话（如重命名）"""
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if request.title is not None:
        session.title = request.title
    
    session.updated_at = datetime.now()
    db.commit()
    db.refresh(session)
    
    logger.info("更新会话", user_id=current_user.id, session_id=session_id)
    
    return SessionResponse(**session.to_dict())


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除会话及所有消息"""
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 级联删除会自动删除关联的消息
    db.delete(session)
    db.commit()
    
    logger.info("删除会话", user_id=current_user.id, session_id=session_id)
    
    return DeleteResponse(success=True, message="会话已删除")


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的所有消息"""
    # 验证会话所有权
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )
    
    logger.info(
        "获取会话消息",
        user_id=current_user.id,
        session_id=session_id,
        count=len(messages)
    )
    
    return MessageListResponse(
        session_id=session_id,
        messages=[MessageResponse(**m.to_dict()) for m in messages]
    )


@router.delete("/{session_id}/messages", response_model=DeleteResponse)
async def clear_session_messages(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空会话的所有消息"""
    # 验证会话所有权
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除所有消息
    db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).delete()
    
    # 更新会话时间
    session.updated_at = datetime.now()
    db.commit()
    
    logger.info("清空会话消息", user_id=current_user.id, session_id=session_id)
    
    return DeleteResponse(success=True, message="消息已清空")
