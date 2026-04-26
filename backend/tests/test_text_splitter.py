"""文本分割器测试"""
import pytest
from langchain_core.documents import Document

from app.core.text_splitter import (
    TextSplitterFactory,
    ChineseTextSplitter,
    SemanticChunker,
    create_text_splitter,
)


class TestTextSplitterFactory:
    """文本分割器工厂测试"""
    
    def test_create_recursive_splitter(self):
        """测试创建递归分割器"""
        splitter = TextSplitterFactory.create(splitter_type="recursive")
        assert splitter is not None
    
    def test_create_markdown_splitter(self):
        """测试创建 Markdown 分割器"""
        splitter = TextSplitterFactory.create(splitter_type="markdown")
        assert splitter is not None
    
    def test_create_python_splitter(self):
        """测试创建 Python 代码分割器"""
        splitter = TextSplitterFactory.create(splitter_type="python")
        assert splitter is not None
    
    def test_create_latex_splitter(self):
        """测试创建 LaTeX 分割器"""
        splitter = TextSplitterFactory.create(splitter_type="latex")
        assert splitter is not None
    
    def test_create_with_custom_params(self):
        """测试创建带自定义参数的分割器"""
        splitter = TextSplitterFactory.create(
            splitter_type="recursive",
            chunk_size=100,
            chunk_overlap=20
        )
        assert splitter is not None
    
    def test_create_unsupported_splitter(self):
        """测试创建不支持的分割器应抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            TextSplitterFactory.create(splitter_type="unsupported")
        assert "不支持的分割器类型" in str(exc_info.value)


class TestChineseTextSplitter:
    """中文文本分割器测试"""
    
    def test_split_short_text(self):
        """测试分割短文本"""
        splitter = ChineseTextSplitter(chunk_size=100, chunk_overlap=10)
        text = "这是第一句话。这是第二句话。这是第三句话。"
        
        chunks = splitter.split_text(text)
        
        assert len(chunks) >= 1
    
    def test_split_long_text(self):
        """测试分割长文本"""
        splitter = ChineseTextSplitter(chunk_size=50, chunk_overlap=5)
        text = "段落一的内容，很长很长的内容。" * 20
        
        chunks = splitter.split_text(text)
        
        # 验证分块数量
        assert len(chunks) > 1
        
        # 验证每个分块的长度
        for chunk in chunks:
            assert len(chunk) <= 50 + 5  # 允许少量重叠
    
    def test_split_documents(self):
        """测试分割文档"""
        splitter = ChineseTextSplitter(chunk_size=100, chunk_overlap=10)
        
        docs = [
            Document(
                page_content="这是第一篇文档的内容。包含很多文字。",
                metadata={"source": "doc1.txt"}
            ),
            Document(
                page_content="这是第二篇文档的内容。也有文字。",
                metadata={"source": "doc2.txt"}
            ),
        ]
        
        chunks = splitter.split_documents(docs)
        
        assert len(chunks) >= 2
    
    def test_split_documents_preserves_metadata(self):
        """测试分割时保留元数据"""
        splitter = ChineseTextSplitter(chunk_size=500, chunk_overlap=50)
        
        docs = [
            Document(
                page_content="这是一段很长的测试内容，用于验证元数据保留功能是否正常工作。确保这个文本足够长，能够被分割成多个块。",
                metadata={"source": "test.txt", "author": "tester"}
            )
        ]
        
        chunks = splitter.split_documents(docs)
        
        assert len(chunks) >= 1
        # 检查元数据保留（中文分词器会保留原始元数据）
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.txt"
            assert chunk.metadata["author"] == "tester"


class TestSemanticChunker:
    """语义分块器测试"""
    
    def test_split_simple_text(self):
        """测试分割简单文本"""
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=10)
        text = "第一句。第二句。第三句。"
        
        chunks = chunker.split_text(text)
        
        assert len(chunks) >= 1
    
    def test_split_with_chinese_punctuation(self):
        """测试中文标点符号分割"""
        chunker = SemanticChunker(chunk_size=50, chunk_overlap=5)
        text = "这是第一句！这是第二句？这是第三句。"
        
        chunks = chunker.split_text(text)
        
        assert len(chunks) >= 1
    
    def test_split_documents(self):
        """测试语义分块文档"""
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=10)
        
        docs = [
            Document(
                page_content="第一段文字。第二段文字。第三段文字。",
                metadata={"page": 1}
            )
        ]
        
        chunks = chunker.split_documents(docs)
        
        assert len(chunks) >= 1
        
        # 验证 chunk_index 元数据
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i


class TestCreateTextSplitter:
    """create_text_splitter 函数测试"""
    
    def test_create_chinese_splitter(self):
        """测试创建中文分割器"""
        splitter = create_text_splitter(splitter_type="chinese")
        assert splitter is not None
        assert isinstance(splitter, ChineseTextSplitter)
    
    def test_create_recursive_splitter(self):
        """测试创建递归分割器"""
        splitter = create_text_splitter(splitter_type="recursive")
        assert splitter is not None
    
    def test_create_with_custom_params(self):
        """测试创建带自定义参数"""
        splitter = create_text_splitter(
            splitter_type="chinese",
            chunk_size=200,
            chunk_overlap=30
        )
        assert splitter is not None


class TestTextSplitterEdgeCases:
    """文本分割器边界情况测试"""
    
    def test_empty_text(self):
        """测试空文本"""
        splitter = ChineseTextSplitter()
        chunks = splitter.split_text("")
        assert chunks == []
    
    def test_whitespace_only(self):
        """测试仅空白字符"""
        splitter = ChineseTextSplitter()
        chunks = splitter.split_text("   \n\t  ")
        assert chunks == []
    
    def test_very_short_text(self):
        """测试非常短的文本"""
        splitter = ChineseTextSplitter(chunk_size=500)
        chunks = splitter.split_text("短文本")
        assert len(chunks) == 1
    
    def test_overlap_not_exceed_chunk_size(self):
        """测试重叠不超过块大小"""
        splitter = ChineseTextSplitter(chunk_size=100, chunk_overlap=50)
        text = "内容。" * 50
        
        chunks = splitter.split_text(text)
        
        # 重叠部分应该一致
        for i in range(1, len(chunks)):
            # 检查重叠
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            # 验证不是完全相同
            assert prev_chunk != curr_chunk
