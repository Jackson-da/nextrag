"""向量存储模块 - Chroma 向量数据库封装"""
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Chroma
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(
        self,
        embedding: Embeddings,
        persist_directory: str | None = None,
        collection_name: str | None = None,
    ):
        settings = get_settings()
        
        self.embedding = embedding
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.collection_name
        self._client: chromadb.PersistentClient | None = None
        self._vectorstore: Chroma | None = None
    
    @property
    def client(self) -> chromadb.PersistentClient:
        """获取 Chroma 客户端"""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
        return self._client
    
    @property
    def vectorstore(self) -> Chroma:
        """获取向量存储实例"""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding,
                persist_directory=self.persist_directory,
            )
        return self._vectorstore
    
    def add_documents(
        self,
        documents: list[Document],
        ids: list[str] | None = None,
        **kwargs
    ) -> list[str]:
        """添加文档到向量库"""
        return self.vectorstore.add_documents(
            documents=documents,
            ids=ids,
            **kwargs
        )
    
    def similarity_search(
        self,
        query: str,
        k: int | None = None,
        filter: dict[str, Any] | None = None,
        **kwargs
    ) -> list[Document]:
        """相似性搜索"""
        settings = get_settings()
        k = k or settings.retrieval_top_k
        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int | None = None,
        filter: dict[str, Any] | None = None,
        **kwargs
    ) -> list[tuple[Document, float]]:
        """带相似度分数的搜索"""
        settings = get_settings()
        k = k or settings.retrieval_top_k
        return self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )
    
    def similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int | None = None,
        **kwargs
    ) -> list[tuple[Document, float]]:
        """带相关性分数的搜索（分数归一化到 0-1）"""
        settings = get_settings()
        k = k or settings.retrieval_top_k
        docs_with_scores = self.similarity_search_with_score(query, k, **kwargs)
        
        # 计算相关性分数
        if not docs_with_scores:
            return []
        
        min_score = min(score for _, score in docs_with_scores)
        max_score = max(score for _, score in docs_with_scores)
        
        if max_score == min_score:
            normalized_scores = [(doc, 1.0) for doc, _ in docs_with_scores]
        else:
            normalized_scores = [
                (doc, (max_score - score) / (max_score - min_score))
                for doc, score in docs_with_scores
            ]
        
        return normalized_scores
    
    def delete(self, ids: list[str] | None = None, **kwargs) -> None:
        """删除向量"""
        if ids:
            self.vectorstore.delete(ids=ids, **kwargs)
    
    def delete_collection(self) -> None:
        """删除整个集合"""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._vectorstore = None
    
    def get_collection_info(self) -> dict[str, Any]:
        """获取集合信息"""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except Exception:
            return {
                "name": self.collection_name,
                "count": 0,
                "metadata": {}
            }
    
    def reset(self) -> None:
        """重置向量库"""
        self.delete_collection()
        self._vectorstore = None
    
    @property
    def as_retriever(self):
        """转换为 LangChain Retriever（全局检索）"""
        settings = get_settings()
        return self.vectorstore.as_retriever(
            search_kwargs={"k": settings.retrieval_top_k}
        )
    
    def get_retriever(self, kb_id: str | None = None):
        """
        获取检索器，支持按知识库过滤
        
        Args:
            kb_id: 知识库 ID，None 表示全局检索
            
        Returns:
            配置好的检索器
        """
        settings = get_settings()
        search_kwargs = {"k": settings.retrieval_top_k}
        
        # 如果指定了知识库，添加过滤条件
        if kb_id:
            search_kwargs["filter"] = {"kb_id": kb_id}
        
        return self.vectorstore.as_retriever(
            search_kwargs=search_kwargs
        )


class MultiCollectionVectorStore:
    """多集合向量存储 - 支持按知识库分库"""
    
    def __init__(
        self,
        embedding: Embeddings,
        persist_directory: str | None = None,
    ):
        settings = get_settings()
        
        self.embedding = embedding
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self._stores: dict[str, VectorStoreManager] = {}
    
    def get_store(self, collection_name: str) -> VectorStoreManager:
        """获取指定集合的向量存储"""
        if collection_name not in self._stores:
            self._stores[collection_name] = VectorStoreManager(
                embedding=self.embedding,
                persist_directory=self.persist_directory,
                collection_name=collection_name,
            )
        return self._stores[collection_name]
    
    def delete_collection(self, collection_name: str) -> None:
        """删除指定集合"""
        if collection_name in self._stores:
            self._stores[collection_name].delete_collection()
            del self._stores[collection_name]
    
    def list_collections(self) -> list[str]:
        """列出所有集合"""
        client = chromadb.PersistentClient(path=self.persist_directory)
        return [col.name for col in client.list_collections()]


def create_vectorstore(
    embedding: Embeddings,
    persist_directory: str | None = None,
    collection_name: str | None = None,
) -> VectorStoreManager:
    """创建向量存储的便捷函数"""
    return VectorStoreManager(
        embedding=embedding,
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
