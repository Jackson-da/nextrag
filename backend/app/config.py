"""应用配置模块 - 使用 Pydantic Settings 进行配置管理"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==================== 环境配置 ====================
    environment: str = Field(
        default="development",
        description="运行环境: development / staging / production"
    )
    
    # ==================== DeepSeek API 配置 ====================
    deepseek_api_key: str = Field(..., description="DeepSeek API 密钥")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API 地址"
    )
    llm_model: str = Field(default="deepseek-chat", description="LLM 模型名称")
    
    # ==================== Embedding 配置 ====================
    embedding_model: str = Field(
        default="BAAI/bge-large-zh-v1.5",
        description="Embedding 模型名称"
    )
    embedding_device: str = Field(default="cpu", description="Embedding 运行设备")
    embedding_batch_size: int = Field(default=32, description="Embedding 批处理大小")
    
    # ==================== 向量数据库配置 ====================
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        description="Chroma 持久化目录"
    )
    collection_name: str = Field(
        default="documents",
        description="向量集合名称"
    )
    
    # ==================== 数据库配置 ====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/documents.db",
        description="数据库连接 URL"
    )
    
    # ==================== Redis 配置 ====================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接 URL"
    )
    redis_enabled: bool = Field(default=False, description="是否启用 Redis")
    redis_max_connections: int = Field(default=50, description="Redis 最大连接数")
    redis_timeout: int = Field(default=30, description="Redis 超时时间(秒)")
    
    # ==================== 服务配置 ====================
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=8000, description="服务监听端口")
    
    # ==================== JWT 认证配置 ====================
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_expire_days: int = Field(default=7, description="Token 过期天数")

    # ==================== 日志配置 ====================
    log_level: str = Field(default="INFO", description="日志级别")
    log_console: bool = Field(default=True, description="是否输出到控制台")
    log_file: bool = Field(default=False, description="是否输出到文件")
    log_file_path: str = Field(default="logs/app.log", description="日志文件路径")
    log_file_max_bytes: int = Field(default=100 * 1024 * 1024, description="单个日志文件最大大小")
    log_file_backup_count: int = Field(default=10, description="保留的日志文件数量")
    log_error_file: bool = Field(default=False, description="是否单独记录错误日志")
    
    # ==================== CORS 配置 ====================
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许的 CORS 源"
    )
    
    # ==================== RAG 配置 ====================
    retrieval_top_k: int = Field(default=5, description="检索返回的最大文档数")
    temperature: float = Field(default=0.3, description="LLM 温度参数")
    max_tokens: int = Field(default=2000, description="LLM 最大输出 Token 数")
    stream: bool = Field(default=True, description="是否启用流式输出")
    
    # ==================== RAG 系统提示词配置 ====================
    rag_system_prompt: str = Field(
        default=(
            "你是一个友善的智能助手，可以帮助用户回答各种问题。\n\n"
            "## 回答原则\n\n"
            "1. **友好亲切**：像朋友聊天一样自然，避免生硬的机器语气\n"
            "2. **善用文档**：如果提供了文档内容且与问题相关，详细解答并适当引用\n"
            "3. **诚实有度**：如果文档信息不足，可以结合常识补充，但不要胡编乱造\n"
            "4. **积极引导**：当没有相关文档或文档信息不足时，引导用户上传相关文档\n"
            "5. **通用问题**：对于常识性问题（如天气、计算、一般知识等），直接用你的知识回答\n"
            "6. **清晰有条理**：回答时可以使用分点、适当加粗让内容更易读\n\n"
            "## 相关文档内容\n\n"
            "{context}\n\n"
            "## 开始回答\n\n"
            "请根据以上原则和问题，友好地回答用户。"
        ),
        description="RAG 系统提示词，{context} 占位符会被替换为检索到的文档内容，留空则表示无相关文档"
    )
    rag_contextualize_prompt: str = Field(
        default=(
            "根据对话历史，将后续问题重写为一个独立的问题。\n\n"
            "规则：\n"
            "1. 如果问题足够清晰，直接返回原问题\n"
            "2. 如果涉及\"它\"、\"这个\"、\"那\"等指代，结合历史确定具体内容\n"
            "3. 保持原意不变。\n\n"
            "对话历史：{chat_history}\n\n"
            "当前问题：{input}\n\n"
            "独立问题："
        ),
        description="历史感知重写提示词，{chat_history} 和 {input} 占位符会自动替换"
    )
    rag_no_context_prompt: str = Field(
        default=(
            "用户问了以下问题：\n{question}\n\n"
            "目前知识库中没有找到与这个问题直接相关的内容。\n\n"
            "请友好地回复用户：\n"
            "1. 先说明知识库暂时没有相关内容，语气轻松自然\n"
            "2. 建议用户可以上传什么类型的文档来丰富知识库\n"
            "3. 尝试用你的知识给出有帮助的回答，但要说明这是基于通用知识的回答\n"
            "4. 鼓励用户上传相关文档，态度积极友好\n\n"
            "回复："
        ),
        description="无相关文档时的回复提示词，{question} 占位符会被替换为用户问题"
    )
    
    # ==================== Embedding 高级配置 ====================
    embedding_query_instruction: str = Field(
        default="为这个句子生成表示以用于检索相关文章：",
        description="Embedding 查询指令"
    )
    embedding_timeout: float = Field(default=60.0, description="Embedding API 超时时间(秒)")
    jina_model: str = Field(
        default="jina-embeddings-v3",
        description="Jina Embedding 模型名称"
    )
    jina_base_url: str = Field(
        default="https://api.jina.ai",
        description="Jina API 地址"
    )
    
    # ==================== 文档处理配置 ====================
    chunk_size: int = Field(default=500, description="文本分块大小")
    chunk_overlap: int = Field(default=50, description="文本分块重叠大小")
    allowed_extensions: list[str] = Field(
        default=[".pdf", ".docx", ".doc", ".txt", ".md"],
        description="允许的文件扩展名"
    )
    max_file_size: int = Field(default=50 * 1024 * 1024, description="最大文件大小 (50MB)")
    
    # ==================== 验证器 ====================
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """温度参数范围校验"""
        if v < 0 or v > 2:
            raise ValueError("temperature 必须在 0-2 之间")
        return v
    
    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """最大 Token 数范围校验"""
        if v < 1 or v > 32000:
            raise ValueError("max_tokens 必须在 1-32000 之间")
        return v
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """端口范围校验"""
        if v < 1 or v > 65535:
            raise ValueError("port 必须在 1-65535 之间")
        return v
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """chunk_overlap 必须小于 chunk_size"""
        # 注意：此时 chunk_size 可能还未加载，使用默认值
        return v
    
    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """最大文件大小校验"""
        max_limit = 100 * 1024 * 1024  # 100MB
        if v > max_limit:
            raise ValueError(f"max_file_size 不能超过 {max_limit // (1024 * 1024)}MB")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """日志级别校验"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level 必须是 {valid_levels} 之一")
        return v.upper()
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """环境配置校验"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"environment 必须是 {valid_envs} 之一")
        return v
    
    # ==================== 属性方法 ====================
    @property
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.environment == "development"
    
    @property
    def effective_log_level(self) -> str:
        """根据环境返回合适的日志级别"""
        if self.is_production:
            return "WARNING"  # 生产默认 WARN
        return self.log_level
    
    @property
    def effective_cors_origins(self) -> list[str]:
        """根据环境返回 CORS 配置"""
        if self.is_production:
            # 生产环境必须有明确的 CORS 配置
            if not self.cors_origins:
                return []
            return self.cors_origins
        return self.cors_origins
    
    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        data_path = Path(self.chroma_persist_directory).parent.absolute()
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    @property
    def chroma_path(self) -> Path:
        """获取 Chroma 数据库路径"""
        path = Path(self.chroma_persist_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def validate_path_security(self) -> None:
        """验证路径安全性，防止路径穿越攻击"""
        paths_to_check = [
            self.chroma_persist_directory,
            str(self.data_dir),
        ]
        
        for path_str in paths_to_check:
            path = Path(path_str).resolve()
            # 检查是否包含危险路径
            path_parts = path.parts
            if ".." in path_parts or any(p.startswith("~") for p in path_parts):
                raise ValueError(f"路径包含非法字符: {path_str}")


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    settings = Settings()
    
    # 运行时安全校验
    settings.validate_path_security()
    
    # JWT 密钥生产环境检查
    if settings.is_production and settings.jwt_secret_key == "your-secret-key-change-in-production":
        import os
        os.environ.pop("JWT_SECRET_KEY", None)  # 清除环境变量以便重新加载
        raise ValueError(
            "生产环境必须设置安全的 JWT_SECRET_KEY！\n"
            "请设置环境变量或 .env 文件中的 jwt_secret_key"
        )
    elif settings.jwt_secret_key == "your-secret-key-change-in-production":
        import warnings
        warnings.warn(
            "警告：使用了默认的 JWT 密钥！\n"
            "生产环境请设置安全的 jwt_secret_key",
            UserWarning
        )
    
    # chunk_overlap 必须小于 chunk_size
    if settings.chunk_overlap >= settings.chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")
    
    return settings
