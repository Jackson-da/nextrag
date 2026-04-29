"""聊天服务 - RAG 对话"""
import json
import time
import uuid
from typing import Any
from datetime import datetime
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_deepseek import ChatDeepSeek
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.rag_chain import RAGChainBuilder
from app.core.vectorstore import VectorStoreManager
from app.core.cache import CacheKeys, delete_cache, get_or_set, get_redis
from app.models.database import SessionLocal
from app.models.chat import ChatSessionModel, ChatMessageModel

import structlog
logger = structlog.get_logger()


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
        self._chat_histories: dict[str, list] = {}  # 内存缓存（用于 RAG 链）
    
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
    
    def _ensure_session(self, session_id: str, user_id: str, kb_id: str | None = None) -> bool:
        """确保会话存在，不存在则创建"""
        db: Session = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id
            ).first()
            
            if not session:
                # 创建新会话
                session = ChatSessionModel(
                    id=session_id,
                    user_id=user_id,
                    title="新对话",
                    knowledge_base_id=kb_id,
                )
                db.add(session)
                db.commit()
                # 清除会话列表缓存
                import asyncio
                asyncio.create_task(delete_cache(CacheKeys.sessions(user_id)))
                return True
            return False
        finally:
            db.close()
    
    def _save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        sources: list | None = None
    ) -> ChatMessageModel:
        """保存消息到数据库"""
        db: Session = SessionLocal()
        try:
            message = ChatMessageModel(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                sources=json.dumps(sources, ensure_ascii=False) if sources else None,
            )
            db.add(message)
            
            # 更新会话的 updated_at
            session = db.query(ChatSessionModel).filter(
                ChatSessionModel.id == session_id
            ).first()
            if session:
                session.updated_at = datetime.now()
                # 如果是第一条用户消息，更新会话标题
                if role == "user" and session.title == "新对话":
                    session.title = content[:30] + ("..." if len(content) > 30 else "")
            
            db.commit()
            db.refresh(message)
            
            # 清除消息缓存（下次加载时获取最新数据）
            import asyncio
            asyncio.create_task(delete_cache(
                CacheKeys.messages(session_id),
                CacheKeys.meta(session_id)
            ))
            
            return message
        finally:
            db.close()
    
    def _load_from_db(self, session_id: str, user_id: str) -> list:
        """从数据库加载会话消息"""
        db: Session = SessionLocal()
        try:
            # 验证会话所有权
            session = db.query(ChatSessionModel).filter(
                ChatSessionModel.id == session_id,
                ChatSessionModel.user_id == user_id
            ).first()
            
            if not session:
                return []
            
            messages = db.query(ChatMessageModel).filter(
                ChatMessageModel.session_id == session_id
            ).order_by(ChatMessageModel.created_at.asc()).all()
            
            # 转换为 LangChain 格式
            chat_history = []
            for msg in messages:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                else:
                    chat_history.append(AIMessage(content=msg.content))
            
            return chat_history
        finally:
            db.close()
    
    async def load_session_messages(self, session_id: str, user_id: str) -> list:
        """从缓存或数据库加载会话消息
        
        优先从 Redis 缓存获取，未命中则从 SQLite 加载并回填缓存
        """
        cache_key = CacheKeys.messages(session_id)
        
        # 尝试从缓存获取
        redis = await get_redis()
        if redis:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    # 转换为 LangChain 格式
                    chat_history = []
                    for msg in data:
                        if msg["role"] == "user":
                            chat_history.append(HumanMessage(content=msg["content"]))
                        else:
                            chat_history.append(AIMessage(content=msg["content"]))
                    self._chat_histories[session_id] = chat_history
                    logger.debug(f"从缓存加载会话: {session_id}")
                    return chat_history
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")
        
        # 未命中，从数据库加载
        chat_history = self._load_from_db(session_id, user_id)
        
        # 回填缓存
        if redis and chat_history:
            try:
                cache_data = [{"role": "user" if isinstance(m, HumanMessage) else "assistant", 
                              "content": m.content} 
                             for m in chat_history]
                await redis.setex(cache_key, CacheKeys.TTL_MESSAGES, json.dumps(cache_data))
                logger.debug(f"缓存写入会话: {session_id}")
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        
        # 更新内存缓存
        self._chat_histories[session_id] = chat_history
        
        return chat_history
    
    async def chat(
        self,
        question: str,
        session_id: str = "default",
        stream: bool = True,
        kb_id: str | None = None,
        user_id: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """处理聊天请求"""
        start_time = time.time()
        
        # 确保会话存在
        self._ensure_session(session_id, user_id, kb_id)
        
        # 获取对话历史（从缓存或数据库）
        if session_id not in self._chat_histories:
            await self.load_session_messages(session_id, user_id)
        chat_history = self._chat_histories.get(session_id, [])
        
        # 获取缓存的 RAG 链
        rag_chain = self._get_rag_chain(kb_id, user_id)
        
        # 调用 RAG 链
        result = await rag_chain.ainvoke(
            input=question,
            chat_history=chat_history,
        )
        
        # 更新对话历史（内存）
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=result["answer"]))
        self._chat_histories[session_id] = chat_history
        
        # 保存消息到数据库
        sources = []
        if "context" in result:
            for doc in result["context"]:
                if isinstance(doc, Document):
                    sources.append({
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata,
                    })
        
        # 保存用户消息
        self._save_message(session_id, user_id, "user", question)
        # 保存 AI 回复
        self._save_message(session_id, user_id, "assistant", result["answer"], sources)
        
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
        """流式聊天"""
        # 确保会话存在
        self._ensure_session(session_id, user_id, kb_id)
        
        # 获取对话历史（从缓存或数据库）
        if session_id not in self._chat_histories:
            await self.load_session_messages(session_id, user_id)
        chat_history = self._chat_histories.get(session_id, [])
        
        # 获取缓存的 RAG 链
        rag_chain = self._get_rag_chain(kb_id, user_id)
        
        # 流式调用
        full_answer = ""
        sources = []
        async for token in rag_chain.astream(
            input=question,
            chat_history=chat_history,
        ):
            full_answer += token
            yield {"event": "message", "data": {"content": token}}
        
        # 更新对话历史（内存）
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=full_answer))
        self._chat_histories[session_id] = chat_history
        
        # 保存消息到数据库
        self._save_message(session_id, user_id, "user", question)
        self._save_message(session_id, user_id, "assistant", full_answer, sources)
        
        yield {"event": "done", "data": {}}
    
    def clear_history(self, session_id: str = "default") -> bool:
        """清除对话历史（内存 + Redis）"""
        import asyncio
        
        # 清除内存
        if session_id in self._chat_histories:
            del self._chat_histories[session_id]
        
        # 异步清除 Redis 缓存
        asyncio.create_task(delete_cache(
            CacheKeys.messages(session_id),
            CacheKeys.meta(session_id)
        ))
        
        return True
    
    def get_history(self, session_id: str = "default") -> list:
        """获取对话历史"""
        return self._chat_histories.get(session_id, [])
    
    async def health_check(self) -> dict[str, bool]:
        """健康检查"""
        result = {"llm": False, "redis": False}
        
        # 检查 LLM
        try:
            await self.llm.ainvoke("ping")
            result["llm"] = True
        except Exception:
            pass
        
        # 检查 Redis
        redis = await get_redis()
        if redis:
            try:
                await redis.ping()
                result["redis"] = True
            except Exception:
                pass
        
        return result


# 全局服务实例（懒加载）
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service