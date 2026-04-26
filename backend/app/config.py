"""应用配置模块 - 使用 Pydantic Settings 进行配置管理"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # DeepSeek API 配置
    deepseek_api_key: str = Field(default="", description="DeepSeek API 密钥")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API 地址"
    )
    llm_model: str = Field(default="deepseek-chat", description="LLM 模型名称")
    
    # Embedding 配置
    embedding_model: str = Field(
        default="BAAI/bge-large-zh-v1.5",
        description="Embedding 模型名称"
    )
    embedding_device: str = Field(default="cpu", description="Embedding 运行设备")
    embedding_batch_size: int = Field(default=32, description="Embedding 批处理大小")
    
    # 向量数据库配置
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        description="Chroma 持久化目录"
    )
    collection_name: str = Field(
        default="documents",
        description="向量集合名称"
    )
    
    # 数据库配置
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/documents.db",
        description="数据库连接 URL"
    )
    
    # Redis 配置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接 URL"
    )
    redis_enabled: bool = Field(default=False, description="是否启用 Redis")
    
    # 服务配置
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=8000, description="服务监听端口")
    log_level: str = Field(default="INFO", description="日志级别")
    
    # CORS 配置
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许的 CORS 源"
    )
    
    # RAG 配置
    retrieval_top_k: int = Field(default=5, description="检索返回的最大文档数")
    temperature: float = Field(default=0.4, description="LLM 温度参数")
    max_tokens: int = Field(default=2000, description="LLM 最大输出 Token 数")
    stream: bool = Field(default=True, description="是否启用流式输出")
    
    # 文档处理配置
    chunk_size: int = Field(default=500, description="文本分块大小")
    chunk_overlap: int = Field(default=50, description="文本分块重叠大小")
    allowed_extensions: list[str] = Field(
        default=[".pdf", ".docx", ".doc", ".txt", ".md"],
        description="允许的文件扩展名"
    )
    max_file_size: int = Field(default=50 * 1024 * 1024, description="最大文件大小 (50MB)")
    
    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        # 使用 chroma_persist_directory 的父目录
        data_path = Path(self.chroma_persist_directory).parent.absolute()
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    @property
    def chroma_path(self) -> Path:
        """获取 Chroma 数据库路径"""
        path = Path(self.chroma_persist_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
