"""Embedding 模型模块 - 文本向量化"""
import httpx

from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from app.config import get_settings

Any = dict | list | str | int | float | bool | None  # 类型别名，仅用于标注


class BGEEmbeddings(Embeddings):
    """BGE Embedding 模型封装 - 使用 LangChain 封装"""
    
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        encode_kwargs: dict[str, Any] | None = None,
        query_instruction: str | None = None,
    ):
        settings = get_settings()
        
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.encode_kwargs = encode_kwargs or {"normalize_embeddings": True}
        self.query_instruction = query_instruction or settings.embedding_query_instruction
        
        # 使用 LangChain 的 HuggingFaceBgeEmbeddings
        self._embedding = HuggingFaceBgeEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.device},
            encode_kwargs=self.encode_kwargs,
            query_instruction=self.query_instruction,
        )

    
    def embed_query(self, text: str) -> list[float]:
        """嵌入单个查询文本"""
        return self._embedding.embed_query(text)
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档"""
        return self._embedding.embed_documents(texts)
    
    def __del__(self):
        """清理模型资源"""
        if hasattr(self, '_embedding'):
            del self._embedding


class JinaEmbeddings(Embeddings):
    """Jina AI Embedding 模型封装 - 使用 Jina API"""
    
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        settings = get_settings()
        
        self.api_key = api_key
        self.model = model or settings.jina_model
        self.base_url = base_url or settings.jina_base_url
        self.timeout = timeout or settings.embedding_timeout
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建异步 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def aembed_query(self, text: str) -> list[float]:
        """异步嵌入单个查询文本"""
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/v1/embeddings",
            headers=self._get_headers(),
            json={
                "model": self.model,
                "input": text
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    
    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """异步批量嵌入文档"""
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/v1/embeddings",
            headers=self._get_headers(),
            json={
                "model": self.model,
                "input": texts
            }
        )
        response.raise_for_status()
        data = response.json()
        # 按原始顺序返回嵌入向量
        embeddings = {item["index"]: item["embedding"] for item in data["data"]}
        return [embeddings[i] for i in range(len(texts))]
    
    def embed_query(self, text: str) -> list[float]:
        """嵌入单个查询文本（同步封装）"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行中的事件循环，直接创建新的
            return asyncio.run(self.aembed_query(text))
        else:
            # 如果有运行中的事件循环，创建一个任务
            future = asyncio.ensure_future(self.aembed_query(text))
            return asyncio.run(future)
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档（同步封装）"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.aembed_documents(texts))
        else:
            future = asyncio.ensure_future(self.aembed_documents(texts))
            return asyncio.run(future)
    
    async def aclose(self):
        """关闭异步客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def __del__(self):
        """清理资源（同步环境）"""
        if self._client and hasattr(self._client, 'close'):
            try:
                self._client.close()
            except Exception:
                pass


def create_embeddings(
    embedding_type: str = "bge",
    **kwargs
) -> Embeddings:
    """创建 Embedding 模型的便捷函数"""
    if embedding_type == "bge":
        return BGEEmbeddings(**kwargs)
    elif embedding_type == "jina":
        return JinaEmbeddings(**kwargs)
    elif embedding_type == "huggingface":
        return HuggingFaceBgeEmbeddings(**kwargs)
    else:
        raise ValueError(f"不支持的 Embedding 类型: {embedding_type}")


# 默认的 BGE 中文 Embedding（单例缓存）
_default_embeddings_instance: BGEEmbeddings | None = None


def get_default_embeddings() -> BGEEmbeddings:
    """获取默认的 BGE Embedding 模型（单例模式，避免重复加载）"""
    global _default_embeddings_instance
    if _default_embeddings_instance is None:
        _default_embeddings_instance = BGEEmbeddings()
    return _default_embeddings_instance
