"""文档服务 - 文档管理和处理"""
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.document_loader import load_document
from app.core.text_splitter import create_text_splitter
from app.core.embeddings import get_default_embeddings
from app.core.vectorstore import VectorStoreManager
from app.models.database import DocumentModel, init_db, SessionLocal


class DocumentService:
    """文档服务类"""

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "documents",
    ):
        settings = get_settings()

        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        self.upload_dir = settings.data_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        init_db()

        # 初始化组件
        self.embedding = get_default_embeddings()
        self.vectorstore = VectorStoreManager(
            embedding=self.embedding,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
        )
        self.text_splitter = create_text_splitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            splitter_type="chinese",
        )
    
    def close(self):
        """关闭文档服务，释放资源"""
        if self.vectorstore is not None:
            self.vectorstore.close()
        self.embedding = None
        self.text_splitter = None

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def _generate_id(self) -> str:
        """生成文档 ID"""
        return str(uuid.uuid4())

    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        return Path(filename).suffix.lower().replace(".", "")

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        description: str | None = None,
        knowledge_base_id: str | None = None,
        user_id: str | None = None,  # 用户关联
    ) -> dict:
        """上传并处理文档"""
        db = self._get_db()
        try:
            # 生成文档 ID
            doc_id = self._generate_id()

            # 保存文件
            safe_filename = f"{doc_id}_{filename}"
            file_path = self.upload_dir / safe_filename

            self.upload_dir.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(file_content)

            # 创建文档记录
            doc_model = DocumentModel(
                id=doc_id,
                user_id=user_id,  # 用户关联
                filename=filename,
                file_path=str(file_path),
                file_size=len(file_content),
                file_type=self._get_file_type(filename),
                description=description,
                status="processing",
                chunk_count=0,
                knowledge_base_id=knowledge_base_id,
            )
            db.add(doc_model)
            db.commit()

            # 添加用户 ID 到元数据
            if user_id:
                self.vectorstore.set_collection_metadata({"user_id": user_id})

            try:
                # 加载文档
                documents = load_document(str(file_path))

                # 分割文档
                chunks = self.text_splitter.split_documents(documents)

                # 添加文档 ID 和知识库 ID 到元数据
                for i, chunk in enumerate(chunks):
                    chunk.metadata["document_id"] = doc_id
                    chunk.metadata["chunk_index"] = i
                    # 添加 kb_id 用于知识库过滤
                    if knowledge_base_id:
                        chunk.metadata["kb_id"] = knowledge_base_id
                    # 添加 user_id 用于用户隔离
                    if user_id:
                        chunk.metadata["user_id"] = user_id

                # 存入向量库
                ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
                self.vectorstore.add_documents(chunks, ids=ids)

                # 更新状态
                doc_model.status = "completed"
                doc_model.chunk_count = len(chunks)

            except Exception as e:
                doc_model.status = "failed"
                doc_model.error = str(e)

            db.commit()
            return doc_model.to_dict()

        finally:
            db.close()

    async def get_document(self, document_id: str) -> dict | None:
        """获取文档信息"""
        db = self._get_db()
        try:
            doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            return doc.to_dict() if doc else None
        finally:
            db.close()

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 20,
        knowledge_base_id: str | None = None,
        user_id: str | None = None,  # 用户关联
    ) -> tuple[list[dict], int]:
        """列出文档（支持用户过滤）"""
        db = self._get_db()
        try:
            query = db.query(DocumentModel)

            # 过滤
            if knowledge_base_id:
                query = query.filter(DocumentModel.knowledge_base_id == knowledge_base_id)
            if user_id:
                query = query.filter(DocumentModel.user_id == user_id)

            # 总数
            total = query.count()

            # 分页并排序
            items = (
                query.order_by(DocumentModel.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            return [item.to_dict() for item in items], total
        finally:
            db.close()

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        db = self._get_db()
        try:
            doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

            if not doc:
                return False

            # 删除文件
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()

            # 从向量库删除
            if doc.chunk_count > 0:
                ids = [f"{document_id}_{i}" for i in range(doc.chunk_count)]
                self.vectorstore.delete(ids=ids)

            # 删除记录
            db.delete(doc)
            db.commit()

            return True
        finally:
            db.close()

    async def get_vectorstore_info(self, user_id: str | None = None) -> dict:
        """获取向量库信息（支持按用户过滤）"""
        # 获取总片段数
        collection_info = self.vectorstore.get_collection_info()
        
        # 如果指定了用户，统计该用户的片段数
        if user_id:
            user_chunk_count = self.vectorstore.get_user_chunk_count(user_id)
            return {
                "name": collection_info["name"],
                "count": user_chunk_count,  # 返回用户自己的片段数
                "metadata": collection_info["metadata"],
            }
        
        return collection_info


# 全局服务实例（懒加载）
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
