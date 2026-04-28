"""聊天服务 - RAG 对话"""
import time
from typing import Any
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_deepseek import ChatDeepSeek

from app.config import get_settings
from app.core.rag_chain import RAGChainBuilder
from app.core.vectorstore import VectorStoreManager


class ChatService:
    """聊天服务类"""
    
    def __init__(
        self,
        vectorstore: VectorStoreManager | None = None,
        collection_name: str = "documents",
    ):
        settings = get_settings()
        
        self.vectorstore = vectorstore
        self.collection_name = collection_name
        self.temperature = settings.temperature
        self.top_k = settings.retrieval_top_k
        
        # LLM 配置
        self.llm_api_key = settings.deepseek_api_key
        self.llm_base_url = settings.deepseek_base_url
        self.llm_model = settings.llm_model
        
        # 懒加载
        self._llm: ChatDeepSeek | None = None
        self._rag_chains: dict[str | None, RAGChainBuilder] = {}  # 按 kb_id 缓存
        self._chat_histories: dict[str, list] = {}
    
    @property
    def llm(self) -> ChatDeepSeek:
        """获取 LLM 实例"""
        if self._llm is None:
            self._llm = ChatDeepSeek(
                model=self.llm_model,
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
                temperature=self.temperature,
                streaming=True,
            )
        return self._llm
    
    @property
    def retriever(self):
        """获取检索器"""
        if self.vectorstore is None:
            from app.services.document_service import get_document_service
            doc_service = get_document_service()
            self.vectorstore = doc_service.vectorstore
        
        return self.vectorstore.as_retriever
    
    @property
    def rag_chain(self) -> RAGChainBuilder:
        """获取 RAG 链"""
        if self._rag_chain is None:
            self._rag_chain = RAGChainBuilder(
                llm=self.llm,
                retriever=self.retriever,
            )
        return self._rag_chain
    
    def _get_rag_chain(self, kb_id: str | None = None, user_id: str | None = None) -> RAGChainBuilder:
        """获取或创建 RAG 链（按 kb_id 和 user_id 缓存）"""
        cache_key = f"{kb_id}:{user_id}"
        if cache_key not in self._rag_chains:
            self._rag_chains[cache_key] = RAGChainBuilder(
                llm=self.llm,
                kb_id=kb_id,
                user_id=user_id,
            )
        return self._rag_chains[cache_key]
    
    async def chat(
        self,
        question: str,
        session_id: str = "default",
        stream: bool = True,
        kb_id: str | None = None,
        user_id: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """处理聊天请求
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            stream: 是否流式输出（未使用，保留接口）
            kb_id: 知识库 ID，None 表示全局检索
            user_id: 用户 ID，用于数据隔离
        """
        start_time = time.time()
        
        # 获取对话历史
        chat_history = self._chat_histories.get(session_id, [])
        
        # 获取缓存的 RAG 链
        rag_chain = self._get_rag_chain(kb_id, user_id)
        
        # 调用 RAG 链
        result = await rag_chain.ainvoke(
            input=question,
            chat_history=chat_history,
        )
        
        # 更新对话历史
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=result["answer"]))
        self._chat_histories[session_id] = chat_history
        
        # 提取来源
        sources = []
        if "context" in result:
            for doc in result["context"]:
                if isinstance(doc, Document):
                    sources.append({
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata,
                    })
        
        latency = time.time() - start_time
        
        return {
            "answer": result["answer"],
            "session_id": session_id,
            "sources": sources,
            "latency": latency,
        }
    
    async def stream_chat(
        self,
        question: str,
        session_id: str = "default",
        kb_id: str | None = None,
        user_id: str | None = None,
        **kwargs
    ):
        """流式聊天
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            kb_id: 知识库 ID，None 表示全局检索
            user_id: 用户 ID，用于数据隔离
        """
        # 获取对话历史
        chat_history = self._chat_histories.get(session_id, [])
        
        # 获取缓存的 RAG 链
        rag_chain = self._get_rag_chain(kb_id, user_id)
        
        # 流式调用
        full_answer = ""
        async for token in rag_chain.astream(
            input=question,
            chat_history=chat_history,
        ):
            full_answer += token
            yield {"event": "message", "data": {"content": token}}
        
        # 更新对话历史
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=full_answer))
        self._chat_histories[session_id] = chat_history
        
        yield {"event": "done", "data": {}}
    
    def clear_history(self, session_id: str = "default") -> bool:
        """清除对话历史"""
        if session_id in self._chat_histories:
            del self._chat_histories[session_id]
            return True
        return False
    
    def get_history(self, session_id: str = "default") -> list:
        """获取对话历史"""
        return self._chat_histories.get(session_id, [])
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 测试 LLM 连接
            await self.llm.ainvoke("ping")
            return True
        except Exception:
            return False


# 全局服务实例（懒加载）
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
