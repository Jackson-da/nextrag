"""文档加载器模块 - 支持多种文档格式"""
import os
from pathlib import Path
from typing import Any, cast
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader


def _try_load_with_encoding(file_path: str) -> list[Document]:
    """尝试用不同编码加载文本文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
    
    for encoding in encodings:
        try:
            loader = TextLoader(file_path, encoding=encoding)
            return loader.load()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # 如果是文件不存在等错误，不再重试
            if "No such file" in str(e) or "不存在" in str(e):
                raise e
            continue
    
    # 所有编码都失败，抛出明确错误
    raise ValueError(
        "无法使用任何已知编码加载文件: " + file_path + "。"
        "请确保文件存在且是有效的文本文件。"
    )


class DocumentLoaderFactory:
    """文档加载器工厂"""

    _loaders: dict[str, type[BaseLoader]] = {
        ".pdf": PyPDFLoader,
        ".docx": UnstructuredWordDocumentLoader,
        ".doc": UnstructuredWordDocumentLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
    }

    @classmethod
    def register(cls, extension: str, loader_class: type[BaseLoader]) -> None:
        """注册新的加载器"""
        cls._loaders[extension.lower()] = loader_class

    @classmethod
    def get_loader(cls, file_path: str) -> BaseLoader:
        """获取对应的加载器"""
        ext = Path(file_path).suffix.lower()

        if ext not in cls._loaders:
            supported = ", ".join(cls._loaders.keys())
            raise ValueError(f"不支持的文件格式: {ext}。支持的格式: {supported}")

        loader_class = cls._loaders[ext]

        # TextLoader 需要明确指定 encoding 参数
        if loader_class == TextLoader:
            return TextLoader(file_path, encoding='utf-8')

        # 使用 cast 避免泛型类型检查问题
        return cast(Any, loader_class)(file_path)

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """获取支持的文件扩展名"""
        return list(cls._loaders.keys())


def load_document(file_path: str) -> list[Document]:
    """加载文档的便捷函数"""
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    ext = Path(file_path).suffix.lower()
    
    # 对于文本文件，使用增强的编码处理
    if ext in {".txt", ".md"}:
        return _try_load_with_encoding(file_path)
    
    # 其他格式使用标准加载器
    loader = DocumentLoaderFactory.get_loader(file_path)
    return loader.load()
