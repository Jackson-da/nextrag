"""文档服务 - 文档管理和处理"""
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from langchain_core.documents import Document

from app.config import get_settings
from app.core.document_loader import load_document
from app.core.text_splitter import create_text_splitter
from app.core.embeddings import get_default_embeddings
from app.core.vectorstore import VectorStoreManager


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
        
        # 内存存储（生产环境应使用数据库）
        self._documents: dict[str, dict] = {}
    
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
    ) -> dict:
        """上传并处理文档"""
        # 生成文档 ID
        doc_id = self._generate_id()
        
        # 保存文件
        safe_filename = f"{doc_id}_{filename}"
        file_path = self.upload_dir / safe_filename
        
        # 确保上传目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 创建文档元数据
        doc_info = {
            "id": doc_id,
            "filename": filename,
            "file_path": str(file_path),
            "file_size": len(file_content),
            "file_type": self._get_file_type(filename),
            "description": description,
            "status": "processing",
            "chunk_count": 0,
            "knowledge_base_id": knowledge_base_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        try:
            # 加载文档
            documents = load_document(str(file_path))
            
            # 分割文档
            chunks = self.text_splitter.split_documents(documents)
            
            # 添加文档 ID 到元数据
            for i, chunk in enumerate(chunks):
                chunk.metadata["document_id"] = doc_id
                chunk.metadata["chunk_index"] = i
            
            # 存入向量库
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            self.vectorstore.add_documents(chunks, ids=ids)
            
            # 更新状态
            doc_info["status"] = "completed"
            doc_info["chunk_count"] = len(chunks)
            doc_info["updated_at"] = datetime.now().isoformat()
            
        except Exception as e:
            doc_info["status"] = "failed"
            doc_info["error"] = str(e)
        
        # 保存文档信息
        self._documents[doc_id] = doc_info
        
        return doc_info
    
    async def get_document(self, document_id: str) -> dict | None:
        """获取文档信息"""
        return self._documents.get(document_id)
    
    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 20,
        knowledge_base_id: str | None = None,
    ) -> tuple[list[dict], int]:
        """列出文档"""
        docs = list(self._documents.values())
        
        # 过滤
        if knowledge_base_id:
            docs = [
                d for d in docs
                if d.get("knowledge_base_id") == knowledge_base_id
            ]
        
        # 排序
        docs.sort(key=lambda x: x["created_at"], reverse=True)
        
        total = len(docs)
        items = docs[skip:skip + limit]
        
        return items, total
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        doc_info = self._documents.get(document_id)
        
        if not doc_info:
            return False
        
        # 删除文件
        file_path = Path(doc_info["file_path"])
        if file_path.exists():
            file_path.unlink()
        
        # 从向量库删除
        chunk_count = doc_info.get("chunk_count", 0)
        if chunk_count > 0:
            ids = [f"{document_id}_{i}" for i in range(chunk_count)]
            self.vectorstore.delete(ids=ids)
        
        # 删除记录
        del self._documents[document_id]
        
        return True
    
    async def get_vectorstore_info(self) -> dict:
        """获取向量库信息"""
        return self.vectorstore.get_collection_info()


# 全局服务实例（懒加载）
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
