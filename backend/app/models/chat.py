"""聊天会话和消息模型"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.database import Base


class ChatSessionModel(Base):
    """聊天会话模型"""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), default="新对话")
    knowledge_base_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联消息
    messages = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.created_at"
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        """转换为字典"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "knowledge_base_id": self.knowledge_base_id,
            "message_count": len(self.messages) if self.messages else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        return result


class ChatMessageModel(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(String(36), nullable=False, index=True)  # 冗余存储，方便查询
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # AI 回复的引用来源，JSON 字符串
    created_at = Column(DateTime, default=datetime.now)

    # 关联会话
    session = relationship("ChatSessionModel", back_populates="messages")

    # 复合索引
    __table_args__ = (
        Index("ix_messages_session_user", "session_id", "user_id"),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        import json
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.sources:
            try:
                result["sources"] = json.loads(self.sources)
            except json.JSONDecodeError:
                result["sources"] = None
        return result
