"""核心模块包"""
from app.core.document_loader import (
    DocumentLoaderFactory,
    load_document,
)
from app.core.text_splitter import (
    TextSplitterFactory,
    ChineseTextSplitter,
    SemanticChunker,
    create_text_splitter,
)
from app.core.embeddings import (
    BGEEmbeddings,
    JinaEmbeddings,
    create_embeddings,
    get_default_embeddings,
)
from app.core.vectorstore import (
    VectorStoreManager,
    MultiCollectionVectorStore,
    create_vectorstore,
)
from app.core.rag_chain import (
    RAGChainBuilder,
    ChatWithHistory,
    create_rag_chain,
    DEFAULT_SYSTEM_PROMPT,
)

__all__ = [
    # Document Loader
    "DocumentLoaderFactory",
    "load_document",
    # Text Splitter
    "TextSplitterFactory",
    "ChineseTextSplitter",
    "SemanticChunker",
    "create_text_splitter",
    # Embeddings
    "BGEEmbeddings",
    "JinaEmbeddings",
    "create_embeddings",
    "get_default_embeddings",
    # VectorStore
    "VectorStoreManager",
    "MultiCollectionVectorStore",
    "create_vectorstore",
    # RAG Chain
    "RAGChainBuilder",
    "ChatWithHistory",
    "create_rag_chain",
    "DEFAULT_SYSTEM_PROMPT",
]
