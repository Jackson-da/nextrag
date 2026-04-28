"""数据库模型测试"""
import pytest
from datetime import datetime

from app.models.database import DocumentModel, KnowledgeBaseModel, SessionLocal, Base, engine


class TestDocumentModel:
    """DocumentModel 测试"""

    def test_create_document(self, db_session, test_user):
        """测试创建文档记录"""
        doc = DocumentModel(
            id="test-doc-123",
            user_id=test_user.id,  # 添加 user_id
            filename="test.pdf",
            file_path="/data/uploads/test-doc-123_test.pdf",
            file_size=1024,
            file_type="pdf",
            description="测试文档",
            status="completed",
            chunk_count=5,
        )
        db_session.add(doc)
        db_session.commit()

        # 验证保存成功
        saved_doc = db_session.query(DocumentModel).filter(DocumentModel.id == "test-doc-123").first()
        assert saved_doc is not None
        assert saved_doc.filename == "test.pdf"
        assert saved_doc.status == "completed"
        assert saved_doc.chunk_count == 5
        assert saved_doc.user_id == test_user.id

    def test_document_to_dict(self, db_session, test_user):
        """测试文档转字典"""
        doc = DocumentModel(
            id="test-doc-456",
            user_id=test_user.id,  # 添加 user_id
            filename="test.docx",
            file_path="/data/uploads/test-doc-456_test.docx",
            file_size=2048,
            status="processing",
        )
        db_session.add(doc)
        db_session.commit()

        doc_dict = doc.to_dict()
        assert doc_dict["id"] == "test-doc-456"
        assert doc_dict["filename"] == "test.docx"
        assert doc_dict["status"] == "processing"
        assert "created_at" in doc_dict
        assert "updated_at" in doc_dict

    def test_delete_document(self, db_session, test_user):
        """测试删除文档"""
        doc = DocumentModel(
            id="test-doc-delete",
            user_id=test_user.id,  # 添加 user_id
            filename="delete.pdf",
            file_path="/data/uploads/test-doc-delete.pdf",
        )
        db_session.add(doc)
        db_session.commit()

        # 删除
        db_session.delete(doc)
        db_session.commit()

        # 验证删除成功
        saved_doc = db_session.query(DocumentModel).filter(DocumentModel.id == "test-doc-delete").first()
        assert saved_doc is None


class TestKnowledgeBaseModel:
    """KnowledgeBaseModel 测试"""

    def test_create_knowledge_base(self, db_session, test_user):
        """测试创建知识库"""
        kb = KnowledgeBaseModel(
            id="test-kb-123",
            user_id=test_user.id,  # 添加 user_id
            name="测试知识库",
            description="这是一个测试知识库",
        )
        db_session.add(kb)
        db_session.commit()

        # 验证保存成功
        saved_kb = db_session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id == "test-kb-123").first()
        assert saved_kb is not None
        assert saved_kb.name == "测试知识库"
        assert saved_kb.description == "这是一个测试知识库"
        assert saved_kb.user_id == test_user.id

    def test_knowledge_base_to_dict(self, db_session, test_user):
        """测试知识库转字典"""
        kb = KnowledgeBaseModel(
            id="test-kb-456",
            user_id=test_user.id,  # 添加 user_id
            name="测试KB",
        )
        db_session.add(kb)
        db_session.commit()

        kb_dict = kb.to_dict()
        assert kb_dict["id"] == "test-kb-456"
        assert kb_dict["name"] == "测试KB"
        assert kb_dict["description"] is None
        assert "created_at" in kb_dict
        assert "updated_at" in kb_dict

    def test_delete_knowledge_base(self, db_session, test_user):
        """测试删除知识库"""
        kb = KnowledgeBaseModel(
            id="test-kb-delete",
            user_id=test_user.id,  # 添加 user_id
            name="待删除知识库",
        )
        db_session.add(kb)
        db_session.commit()

        # 删除
        db_session.delete(kb)
        db_session.commit()

        # 验证删除成功
        saved_kb = db_session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id == "test-kb-delete").first()
        assert saved_kb is None


class TestDatabaseSession:
    """数据库会话测试"""

    def test_session_context_manager(self):
        """测试会话上下文管理器"""
        db = SessionLocal()
        try:
            # 执行查询
            count = db.query(DocumentModel).count()
            assert count >= 0  # 只要不报错就行
        finally:
            db.close()

    def test_query_with_filter(self, db_session, test_user):
        """测试带过滤条件的查询"""
        # 创建测试数据
        doc = DocumentModel(
            id="test-filter-1",
            user_id=test_user.id,  # 添加 user_id
            filename="filter_test.pdf",
            file_path="/data/uploads/filter_test.pdf",
            knowledge_base_id="kb-123",
        )
        db_session.add(doc)
        db_session.commit()

        # 查询特定知识库的文档
        docs = db_session.query(DocumentModel).filter(
            DocumentModel.knowledge_base_id == "kb-123"
        ).all()

        assert len(docs) >= 1
        assert all(d.knowledge_base_id == "kb-123" for d in docs)

    def test_query_with_order(self, db_session, test_user):
        """测试带排序的查询"""
        # 创建测试数据
        doc1 = DocumentModel(
            id="test-order-1",
            user_id=test_user.id,  # 添加 user_id
            filename="order1.pdf",
            file_path="/data/uploads/order1.pdf",
        )
        doc2 = DocumentModel(
            id="test-order-2",
            user_id=test_user.id,  # 添加 user_id
            filename="order2.pdf",
            file_path="/data/uploads/order2.pdf",
        )
        db_session.add(doc1)
        db_session.add(doc2)
        db_session.commit()

        # 按创建时间排序
        docs = db_session.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        assert len(docs) >= 2
