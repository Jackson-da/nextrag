"""文档加载器测试"""
import pytest
import tempfile
from pathlib import Path
from langchain_core.documents import Document

from app.core.document_loader import (
    DocumentLoaderFactory,
    PDFLoader,
    DocxLoader,
    TextLoader,
    load_document,
)


class TestDocumentLoaderFactory:
    """文档加载器工厂测试"""
    
    def test_get_loader_for_pdf(self):
        """测试获取 PDF 加载器"""
        loader = DocumentLoaderFactory.get_loader("test.pdf")
        assert isinstance(loader, PDFLoader)
    
    def test_get_loader_for_docx(self):
        """测试获取 DOCX 加载器"""
        loader = DocumentLoaderFactory.get_loader("test.docx")
        assert isinstance(loader, DocxLoader)
    
    def test_get_loader_for_txt(self):
        """测试获取文本加载器"""
        loader = DocumentLoaderFactory.get_loader("test.txt")
        assert isinstance(loader, TextLoader)
    
    def test_get_loader_for_md(self):
        """测试获取 Markdown 加载器"""
        loader = DocumentLoaderFactory.get_loader("test.md")
        assert isinstance(loader, TextLoader)
    
    def test_get_loader_uppercase_extension(self):
        """测试大写扩展名"""
        loader = DocumentLoaderFactory.get_loader("test.PDF")
        assert isinstance(loader, PDFLoader)
    
    def test_get_loader_unsupported(self):
        """测试不支持的文件类型"""
        with pytest.raises(ValueError) as exc_info:
            DocumentLoaderFactory.get_loader("test.xyz")
        assert "不支持" in str(exc_info.value)
    
    def test_supported_extensions(self):
        """测试支持的扩展名列表"""
        extensions = DocumentLoaderFactory.supported_extensions()
        
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".txt" in extensions
        assert ".md" in extensions


class TestTextLoader:
    """文本加载器测试"""
    
    def test_load_text_file(self):
        """测试加载文本文件"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            encoding='utf-8',
            delete=False
        ) as f:
            f.write("这是测试文件的内容。")
            temp_path = f.name
        
        try:
            loader = TextLoader(temp_path)
            docs = loader.load()
            
            assert len(docs) == 1
            assert "这是测试文件的内容。" in docs[0].page_content
            assert docs[0].metadata["source"] == temp_path
            assert docs[0].metadata["file_type"] == "txt"
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_text_file(self):
        """测试加载空文本文件"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False
        ) as f:
            temp_path = f.name
        
        try:
            loader = TextLoader(temp_path)
            docs = loader.load()
            
            assert len(docs) == 1
            assert docs[0].page_content == ""
        finally:
            Path(temp_path).unlink()
    
    def test_load_text_file_with_encoding(self):
        """测试指定编码加载文本文件"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            encoding='gbk',
            delete=False
        ) as f:
            f.write("中文内容测试")
            temp_path = f.name
        
        try:
            loader = TextLoader(temp_path, encoding='gbk')
            docs = loader.load()
            
            assert "中文内容测试" in docs[0].page_content
        finally:
            Path(temp_path).unlink()


class TestLoadDocument:
    """load_document 函数测试"""
    
    def test_load_txt_document(self):
        """测试加载 TXT 文档"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            encoding='utf-8',
            delete=False
        ) as f:
            f.write("TXT 文档内容")
            temp_path = f.name
        
        try:
            docs = load_document(temp_path)
            
            assert len(docs) >= 1
            assert "TXT 文档内容" in docs[0].page_content
        finally:
            Path(temp_path).unlink()
    
    def test_load_markdown_document(self):
        """测试加载 Markdown 文档"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            encoding='utf-8',
            delete=False
        ) as f:
            f.write("# 标题\n\n这是 Markdown 内容。")
            temp_path = f.name
        
        try:
            docs = load_document(temp_path)
            
            assert len(docs) >= 1
            assert "Markdown 内容" in docs[0].page_content
        finally:
            Path(temp_path).unlink()


class TestDocumentLoaderEdgeCases:
    """文档加载器边界情况测试"""
    
    def test_filename_with_path(self):
        """测试带路径的文件名"""
        loader = DocumentLoaderFactory.get_loader("/path/to/document.pdf")
        assert isinstance(loader, PDFLoader)
    
    def test_filename_with_windows_path(self):
        """测试 Windows 路径"""
        loader = DocumentLoaderFactory.get_loader("C:\\Users\\test\\document.pdf")
        assert isinstance(loader, PDFLoader)
    
    def test_filename_with_spaces(self):
        """测试带空格的文件名"""
        loader = DocumentLoaderFactory.get_loader("my document.pdf")
        assert isinstance(loader, PDFLoader)
