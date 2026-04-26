"""Embedding 模型模块 - 文本向量化"""
from typing import Any
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings


class BGEEmbeddings(Embeddings):
    """BGE Embedding 模型封装 - 使用 LangChain 封装"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        device: str = "cpu",
        encode_kwargs: dict[str, Any] | None = None,
        query_instruction: str = "为这个句子生成表示以用于检索相关文章：",
    ):
        self.model_name = model_name
        self.device = device
        self.encode_kwargs = encode_kwargs or {"normalize_embeddings": True}
        self.query_instruction = query_instruction
        
        # 使用 LangChain 的 HuggingFaceBgeEmbeddings
        self._embedding = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs=self.encode_kwargs,
            query_instruction=query_instruction,
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
        model: str = "jina-embeddings-v3",
        base_url: str = "https://api.jina.ai",
    ):
        import httpx
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = httpx.Client(timeout=60.0)
    
    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def embed_query(self, text: str) -> list[float]:
        """嵌入单个查询文本"""
        response = self._client.post(
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
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档"""
        response = self._client.post(
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
    
    def __del__(self):
        self._client.close()


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


# 默认的 BGE 中文 Embedding
def get_default_embeddings() -> BGEEmbeddings:
    """获取默认的 BGE Embedding 模型"""
    return BGEEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5",
        device="cpu",
        encode_kwargs={"normalize_embeddings": True}
    )
