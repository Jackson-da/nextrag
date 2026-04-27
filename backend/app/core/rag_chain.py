"""RAG 链模块 - 检索增强生成"""
import asyncio
from collections.abc import AsyncIterator
from typing import Any
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain  # type: ignore[import]
from langchain_classic.chains.combine_documents import create_stuff_documents_chain  # type: ignore[import]
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.config import get_settings


# 提示词获取超时常量（秒）
TOKEN_QUEUE_TIMEOUT = 1.0


class RAGChainBuilder:
    """RAG 链构建器"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Any,
        system_prompt: str | None = None,
        contextualize_q_system_prompt: str | None = None,
    ):
        settings = get_settings()
        
        self.llm = llm
        self.retriever = retriever
        self.system_prompt = system_prompt or settings.rag_system_prompt
        self.contextualize_q_system_prompt = contextualize_q_system_prompt or settings.rag_contextualize_prompt
        self.no_context_prompt = settings.rag_no_context_prompt
        self._chain: Any | None = None
        self._history_aware_retriever: Any | None = None
    
    def build(self) -> Any:
        """构建 RAG 链"""
        if self._chain is not None:
            return self._chain
        
        # 构建历史感知检索器（简化版本）
        history_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        self._history_aware_retriever = create_history_aware_retriever(
            llm=self.llm,
            retriever=self.retriever,
            prompt=history_prompt,
        )
        
        # 构建问答链
        qa_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            ("human", "{context}\n\n用户问题：{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=qa_prompt,
            document_variable_name="context",
        )
        
        # 构建完整 RAG 链
        self._chain = create_retrieval_chain(
            retriever=self._history_aware_retriever,
            combine_docs_chain=question_answer_chain,
        )
        
        return self._chain
    
    @property
    def chain(self) -> Any:
        """获取 RAG 链"""
        if self._chain is None:
            self.build()
        return self._chain
    
    def _has_context(self, result: dict[str, Any]) -> bool:
        """检查检索结果是否有有效上下文"""
        docs = result.get("context", [])
        if not docs:
            return False
        # 检查文档内容是否为空或只有空白
        for doc in docs:
            if doc.page_content and doc.page_content.strip():
                return True
        return False
    
    def _build_no_context_response(self, question: str) -> str:
        """构建无上下文时的响应"""
        prompt = self.no_context_prompt.format(question=question)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    def invoke(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """同步调用 RAG 链"""
        result = self.chain.invoke(
            {"input": input, "chat_history": chat_history or []},
            **kwargs
        )
        
        # 检查是否有有效上下文
        if not self._has_context(result):
            answer = self._build_no_context_response(input)
            return {
                "answer": answer,
                "context": [],
                "sources": [],
            }
        
        return result
    
    async def ainvoke(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """异步调用 RAG 链"""
        result = await self.chain.ainvoke(
            {"input": input, "chat_history": chat_history or []},
            **kwargs
        )
        
        # 检查是否有有效上下文
        if not self._has_context(result):
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None,
                self._build_no_context_response,
                input
            )
            return {
                "answer": answer,
                "context": [],
                "sources": [],
            }
        
        return result
    
    async def astream(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """异步流式调用 RAG 链"""
        try:
            # 确保链已构建
            if self._history_aware_retriever is None:
                self.build()
            
            # 先检索文档
            retrieved_docs = await self._history_aware_retriever.ainvoke(
                {"input": input, "chat_history": chat_history or []}
            )
            
            # 检查检索结果
            has_docs = any(doc.page_content and doc.page_content.strip() for doc in retrieved_docs)
            
            if not has_docs:
                # 无相关文档，生成友好回复
                loop = asyncio.get_event_loop()
                answer = await loop.run_in_executor(
                    None,
                    self._build_no_context_response,
                    input
                )
                yield answer
                return
            
            # 有文档，使用标准流程
            async for chunk in self.chain.astream(
                {"input": input, "chat_history": chat_history or []},
                **kwargs
            ):
                if "answer" in chunk:
                    yield chunk["answer"]
        except Exception as e:
            yield f"检索服务出错: {str(e)}"


class StreamingCallbackHandler(AsyncCallbackHandler):
    """流式输出回调处理器"""
    
    def __init__(self):
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.done = False
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """LLM 生成新 token 时调用"""
        await self.queue.put(token)
    
    async def get_tokens(self) -> AsyncIterator[str]:
        """获取生成的 tokens"""
        while not self.done or not self.queue.empty():
            try:
                token = await asyncio.wait_for(self.queue.get(), timeout=TOKEN_QUEUE_TIMEOUT)
                yield token
            except asyncio.TimeoutError:
                if self.done:
                    break


class ChatWithHistory:
    """带对话历史的聊天"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Any,
        redis_url: str | None = None,
        session_id: str = "default",
        system_prompt: str | None = None,
    ):
        settings = get_settings()
        
        self.llm = llm
        self.retriever = retriever
        self.session_id = session_id
        self.system_prompt = system_prompt or settings.rag_system_prompt
        self.no_context_prompt = settings.rag_no_context_prompt
        
        # 初始化消息历史
        if redis_url:
            from langchain_redis import RedisChatMessageHistory  # type: ignore[import]
            self.message_history = RedisChatMessageHistory(
                url=redis_url,
                session_id=session_id,
            )
        else:
            from langchain_community.chat_message_histories import ChatMessageHistory  # type: ignore[import]
            self.message_history = ChatMessageHistory()
        
        # 构建链
        self.rag_builder = RAGChainBuilder(
            llm=self.llm,
            retriever=self.retriever,
            system_prompt=self.system_prompt,
        )
        self.chain = self.rag_builder.chain
        
        # 添加历史管理
        self.chain_with_history = RunnableWithMessageHistory(
            runnable=self.chain,
            get_session_history=lambda session_id: self.message_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    
    def _has_context(self, docs: list) -> bool:
        """检查是否有有效上下文"""
        if not docs:
            return False
        return any(doc.page_content and doc.page_content.strip() for doc in docs)
    
    def _build_no_context_response(self, question: str) -> str:
        """构建无上下文时的响应"""
        prompt = self.no_context_prompt.format(question=question)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    def chat(self, question: str) -> dict[str, Any]:
        """聊天（同步）"""
        config = {"configurable": {"session_id": self.session_id}}
        
        response = self.chain_with_history.invoke(
            {"input": question},
            config=config
        )
        
        # 检查是否有有效上下文
        docs = response.get("context", [])
        if not self._has_context(docs):
            answer = self._build_no_context_response(question)
            return {
                "answer": answer,
                "context": [],
                "chat_history": self.message_history.messages,
            }
        
        return {
            "answer": response["answer"],
            "context": docs,
            "chat_history": self.message_history.messages,
        }
    
    async def achat(self, question: str) -> dict[str, Any]:
        """聊天（异步）"""
        config = {"configurable": {"session_id": self.session_id}}
        
        response = await self.chain_with_history.ainvoke(
            {"input": question},
            config=config
        )
        
        # 检查是否有有效上下文
        docs = response.get("context", [])
        if not self._has_context(docs):
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(
                None,
                self._build_no_context_response,
                question
            )
            return {
                "answer": answer,
                "context": [],
                "chat_history": self.message_history.messages,
            }
        
        return {
            "answer": response["answer"],
            "context": docs,
            "chat_history": self.message_history.messages,
        }
    
    def clear_history(self) -> None:
        """清除对话历史"""
        self.message_history.clear()


def create_rag_chain(
    llm_api_key: str,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    retriever: Any = None,
    temperature: float | None = None,
    system_prompt: str | None = None,
) -> RAGChainBuilder:
    """创建 RAG 链的便捷函数"""
    settings = get_settings()
    
    # 使用配置中的默认值
    base_url = llm_base_url or settings.deepseek_base_url
    model = llm_model or settings.llm_model
    temp = temperature if temperature is not None else settings.temperature
    
    # 创建 LLM
    llm = ChatDeepSeek(
        model=model,
        api_key=llm_api_key,
        base_url=base_url,
        temperature=temp,
        streaming=True,
    )
    
    # 构建 RAG 链
    return RAGChainBuilder(
        llm=llm,
        retriever=retriever,
        system_prompt=system_prompt,
    )


def get_default_prompt(prompt_type: str = "system") -> str:
    """
    获取默认提示词
    
    Args:
        prompt_type: 提示词类型，"system" 或 "contextualize"
    
    Returns:
        对应类型的默认提示词
    """
    settings = get_settings()
    if prompt_type == "contextualize":
        return settings.rag_contextualize_prompt
    return settings.rag_system_prompt
