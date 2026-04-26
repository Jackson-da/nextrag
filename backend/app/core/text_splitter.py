"""文本分割器模块 - 智能文档分块"""
from collections.abc import Callable
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    Language,
)
from langchain_text_splitters.base import TextSplitter


class TextSplitterFactory:
    """文本分割器工厂"""

    @classmethod
    def create(
        cls,
        splitter_type: str = "recursive",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        length_function: Callable[[str], int] = len,
        **kwargs
    ) -> TextSplitter:
        """创建文本分割器"""
        if splitter_type == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=length_function,
                **kwargs
            )
        elif splitter_type == "markdown":
            return MarkdownTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=length_function,
                **kwargs
            )
        elif splitter_type == "python":
            # 使用 RecursiveCharacterTextSplitter 配合 Python 语言
            return RecursiveCharacterTextSplitter.from_language(
                language=Language.PYTHON,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=length_function,
                **kwargs
            )
        elif splitter_type == "latex":
            return RecursiveCharacterTextSplitter.from_language(
                language=Language.LATEX,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=length_function,
                **kwargs
            )
        else:
            available = ["recursive", "markdown", "python", "latex"]
            raise ValueError(f"不支持的分割器类型: {splitter_type}。可用: {available}")


class ChineseTextSplitter(RecursiveCharacterTextSplitter):
    """中文文本分割器 - 针对中文优化的分割器"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
        **kwargs
    ):
        # 中文优化的分隔符
        if separators is None:
            separators = [
                "\n\n",      # 段落分隔
                "\n",        # 换行分隔
                "。",        # 句号
                "！",        # 感叹号
                "？",        # 问号
                "；",        # 分号
                "，",        # 逗号
                " ",         # 空格
                ""           # 按字符分割
            ]
        
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            **kwargs
        )


class SemanticChunker:
    """语义分块器 - 基于句子边界的智能分块"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        sentences_separator: str = "。！？",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentences_separator = sentences_separator
    
    def split_text(self, text: str) -> list[str]:
        """分割文本"""
        import re
        
        # 按句子分割
        sentence_pattern = f"[{self.sentences_separator}]+"
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果当前句子加上现有内容超过块大小
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个句子超过块大小，进一步分割
                if len(sentence) > self.chunk_size:
                    # 按字符分割
                    for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                        chunks.append(sentence[i:i + self.chunk_size])
                    current_chunk = ""
                else:
                    # 开启新块，但保留重叠部分
                    current_chunk = sentence[-self.chunk_overlap:] if self.chunk_overlap else ""
                    if current_chunk:
                        current_chunk = sentence[:self.chunk_overlap] + current_chunk
                    else:
                        current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += sentence
                else:
                    current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """分割文档列表"""
        result = []
        
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                result.append(Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                ))
        
        return result


def create_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    splitter_type: str = "chinese"
) -> TextSplitter:
    """创建文本分割器的便捷函数"""
    if splitter_type == "chinese":
        return ChineseTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    return TextSplitterFactory.create(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
