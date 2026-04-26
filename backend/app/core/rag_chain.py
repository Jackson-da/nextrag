"""RAG 链模块 - 检索增强生成"""
from typing import Any, AsyncIterator, Optional, Literal
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory


# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是一个专业的文档问答助手。

请遵循以下规则：
1. 只根据提供的上下文信息回答问题，不要编造信息
2. 如果上下文中没有相关信息，明确告知用户"抱歉，我没有找到相关信息"
3. 回答要准确、简洁、有条理
4. 适当引用文档来源，帮助用户理解答案出处

{context}"""


# 历史感知的系统提示词
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """根据对话历史，将后续问题重写为一个独立的问题。
重写时需要考虑：
1. 如果用户问题已经足够清晰，直接返回原问题
2. 如果问题涉及"它"、"这个"、"那"等指代，需要结合历史确定具体指代内容
3. 保持问题的语义不变

对话历史：
{chat_history}

用户问题：{input}

独立问题："""


class RAGChainBuilder:
    """RAG 链构建器"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Any,
        system_prompt: str | None = None,
        contextualize_q_system_prompt: str | None = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.contextualize_q_system_prompt = (
            contextualize_q_system_prompt or CONTEXTUALIZE_Q_SYSTEM_PROMPT
        )
        self._chain: Optional[Any] = None
        self._history_aware_retriever: Optional[Any] = None
    
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
    
    def invoke(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """同步调用 RAG 链"""
        return self.chain.invoke(
            {"input": input, "chat_history": chat_history or []},
            **kwargs
        )
    
    async def ainvoke(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """异步调用 RAG 链"""
        return await self.chain.ainvoke(
            {"input": input, "chat_history": chat_history or []},
            **kwargs
        )
    
    async def astream(
        self,
        input: str,
        chat_history: list[BaseMessage] | None = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """异步流式调用 RAG 链"""
        try:
            async for chunk in self.chain.astream(
                {"input": input, "chat_history": chat_history or []},
                **kwargs
            ):
                if "answer" in chunk:
                    yield chunk["answer"]
        except Exception as e:
            # 检索失败时，返回错误提示
            error_msg = f"检索服务出错: {str(e)}"
            yield error_msg


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
                token = await asyncio.wait_for(self.queue.get(), timeout=1.0)
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
        self.llm = llm
        self.retriever = retriever
        self.session_id = session_id
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        
        # 初始化消息历史
        if redis_url:
            self.message_history = RedisChatMessageHistory(
                url=redis_url,
                session_id=session_id,
            )
        else:
            from langchain.memory import ChatMessageHistory
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
    
    def chat(self, question: str) -> dict[str, Any]:
        """聊天（同步）"""
        config = {"configurable": {"session_id": self.session_id}}
        
        response = self.chain_with_history.invoke(
            {"input": question},
            config=config
        )
        
        return {
            "answer": response["answer"],
            "context": response.get("context", []),
            "chat_history": self.message_history.messages,
        }
    
    async def achat(self, question: str) -> dict[str, Any]:
        """聊天（异步）"""
        config = {"configurable": {"session_id": self.session_id}}
        
        response = await self.chain_with_history.ainvoke(
            {"input": question},
            config=config
        )
        
        return {
            "answer": response["answer"],
            "context": response.get("context", []),
            "chat_history": self.message_history.messages,
        }
    
    def clear_history(self) -> None:
        """清除对话历史"""
        self.message_history.clear()


def create_rag_chain(
    llm_api_key: str,
    llm_base_url: str = "https://api.deepseek.com/v1",
    llm_model: str = "deepseek-chat",
    retriever: Any = None,
    temperature: float = 0.0,
    system_prompt: str | None = None,
) -> RAGChainBuilder:
    """创建 RAG 链的便捷函数"""
    import os
    
    # 创建 LLM
    llm = ChatDeepSeek(
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url,
        temperature=temperature,
        streaming=True,
    )
    
    # 构建 RAG 链
    return RAGChainBuilder(
        llm=llm,
        retriever=retriever,
        system_prompt=system_prompt,
    )


import asyncio
