"""数据模型测试"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    DocumentStatus,
    DocumentBase,
    DocumentCreate,
    DocumentResponse,
    ChatRequest,
    ChatResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    HealthResponse,
    ErrorResponse,
    UploadResponse,
    DeleteResponse,
)


class TestDocumentStatus:
    """文档状态枚举测试"""
    
    def test_document_status_values(self):
        """测试文档状态枚举值"""
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.COMPLETED.value == "completed"
        assert DocumentStatus.FAILED.value == "failed"


class TestDocumentSchemas:
    """文档模型测试"""
    
    def test_document_base_valid(self):
        """测试有效的 DocumentBase"""
        doc = DocumentBase(
            filename="test.pdf",
            description="测试文档"
        )
        assert doc.filename == "test.pdf"
        assert doc.description == "测试文档"
    
    def test_document_base_without_description(self):
        """测试 DocumentBase（无描述）"""
        doc = DocumentBase(filename="test.pdf")
        assert doc.filename == "test.pdf"
        assert doc.description is None
    
    def test_document_create_valid(self):
        """测试有效的 DocumentCreate"""
        doc = DocumentCreate(
            filename="test.pdf",
            description="测试",
            knowledge_base_id="kb-123"
        )
        assert doc.filename == "test.pdf"
        assert doc.knowledge_base_id == "kb-123"
    
    def test_document_response_valid(self):
        """测试有效的 DocumentResponse"""
        doc = DocumentResponse(
            id="doc-123",
            filename="test.pdf",
            file_path="/path/to/file.pdf",
            file_size=1024,
            file_type="pdf",
            status=DocumentStatus.COMPLETED,
            chunk_count=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert doc.id == "doc-123"
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.chunk_count == 5


class TestChatSchemas:
    """聊天模型测试"""
    
    def test_chat_request_valid(self):
        """测试有效的 ChatRequest"""
        request = ChatRequest(
            question="这是一个问题？",
            session_id="session-123",
            stream=True
        )
        assert request.question == "这是一个问题？"
        assert request.session_id == "session-123"
        assert request.stream is True
    
    def test_chat_request_empty_question(self):
        """测试空问题应失败"""
        with pytest.raises(ValidationError):
            ChatRequest(
                question="",
                session_id="session-123"
            )
    
    def test_chat_request_question_too_long(self):
        """测试问题过长应失败"""
        with pytest.raises(ValidationError):
            ChatRequest(
                question="x" * 3000,  # 超过 2000 字符限制
                session_id="session-123"
            )
    
    def test_chat_response_valid(self):
        """测试有效的 ChatResponse"""
        response = ChatResponse(
            answer="这是回答",
            session_id="session-123",
            sources=[],
            latency=1.5
        )
        assert response.answer == "这是回答"
        assert response.latency == 1.5


class TestKnowledgeBaseSchemas:
    """知识库模型测试"""
    
    def test_knowledge_base_create_valid(self):
        """测试有效的 KnowledgeBaseCreate"""
        kb = KnowledgeBaseCreate(
            name="测试知识库",
            description="这是一个测试"
        )
        assert kb.name == "测试知识库"
        assert kb.description == "这是一个测试"
    
    def test_knowledge_base_create_empty_name(self):
        """测试空名称应失败"""
        with pytest.raises(ValidationError):
            KnowledgeBaseCreate(name="")
    
    def test_knowledge_base_create_name_too_long(self):
        """测试名称过长应失败"""
        with pytest.raises(ValidationError):
            KnowledgeBaseCreate(name="x" * 150)
    
    def test_knowledge_base_update_valid(self):
        """测试有效的 KnowledgeBaseUpdate"""
        update = KnowledgeBaseUpdate(
            name="新名称",
            description="新描述"
        )
        assert update.name == "新名称"
        assert update.description == "新描述"
    
    def test_knowledge_base_update_partial(self):
        """测试部分更新"""
        update = KnowledgeBaseUpdate(name="仅更新名称")
        assert update.name == "仅更新名称"
        assert update.description is None
    
    def test_knowledge_base_response_valid(self):
        """测试有效的 KnowledgeBaseResponse"""
        kb = KnowledgeBaseResponse(
            id="kb-123",
            name="测试知识库",
            description="描述",
            document_count=5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert kb.id == "kb-123"
        assert kb.document_count == 5


class TestResponseSchemas:
    """响应模型测试"""
    
    def test_health_response_valid(self):
        """测试有效的 HealthResponse"""
        health = HealthResponse(
            status="healthy",
            version="1.0.0",
            llm_connected=True,
            vectorstore_connected=True,
            document_count=10
        )
        assert health.status == "healthy"
        assert health.document_count == 10
    
    def test_error_response_valid(self):
        """测试有效的 ErrorResponse"""
        error = ErrorResponse(
            error="ValidationError",
            message="验证失败",
            detail="字段 xxx 必填"
        )
        assert error.error == "ValidationError"
    
    def test_upload_response_valid(self):
        """测试有效的 UploadResponse"""
        upload = UploadResponse(
            document_id="doc-123",
            filename="test.pdf",
            status="success",
            message="上传成功"
        )
        assert upload.document_id == "doc-123"
    
    def test_delete_response_valid(self):
        """测试有效的 DeleteResponse"""
        delete = DeleteResponse(
            success=True,
            message="删除成功"
        )
        assert delete.success is True
