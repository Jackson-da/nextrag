"""Pydantic 数据模型定义"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    PENDING = "pending"      # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


class DocumentBase(BaseModel):
    """文档基础模型"""
    filename: str = Field(..., description="文件名")
    description: str | None = Field(None, description="文档描述")


class DocumentCreate(DocumentBase):
    """创建文档请求模型"""
    knowledge_base_id: str | None = Field(None, description="知识库 ID")


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="文档 ID")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小 (字节)")
    file_type: str | None = Field(None, description="文件类型")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(default=0, description="分块数量")
    knowledge_base_id: str | None = Field(None, description="知识库 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: dict[str, Any] | None = Field(default=None, description="元数据")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int = Field(..., description="总数")
    items: list[DocumentResponse] = Field(..., description="文档列表")


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    created_at: datetime | None = Field(None, description="创建时间")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: str = Field(..., description="会话 ID")
    knowledge_base_id: str | None = Field(None, description="指定知识库 ID")
    stream: bool = Field(default=True, description="是否流式输出")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    answer: str = Field(..., description="AI 回答")
    session_id: str = Field(..., description="会话 ID")
    sources: list[dict[str, Any]] = Field(default=[], description="引用来源")
    tokens_used: int | None = Field(None, description="使用的 Token 数")
    latency: float = Field(..., description="响应延迟 (秒)")


class ChatStreamResponse(BaseModel):
    """流式聊天响应模型"""
    event: str = Field(..., description="事件类型")
    data: dict[str, Any] = Field(..., description="事件数据")


class KnowledgeBaseBase(BaseModel):
    """知识库基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: str | None = Field(None, description="知识库描述")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """创建知识库请求模型"""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求模型"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """知识库响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="知识库 ID")
    document_count: int = Field(default=0, description="文档数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    total: int = Field(..., description="总数")
    items: list[KnowledgeBaseResponse] = Field(..., description="知识库列表")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    llm_connected: bool = Field(..., description="LLM 连接状态")
    vectorstore_connected: bool = Field(..., description="向量库连接状态")
    document_count: int = Field(default=0, description="文档数量")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: str | None = Field(None, description="详细错误信息")


class UploadResponse(BaseModel):
    """文件上传响应"""
    document_id: str = Field(..., description="文档 ID")
    filename: str = Field(..., description="文件名")
    status: str = Field(..., description="上传状态")
    message: str = Field(..., description="提示信息")


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
