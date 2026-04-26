"""配置模块测试"""
import pytest
from pathlib import Path

from app.config import Settings, get_settings


class TestSettings:
    """配置类测试"""
    
    def test_default_settings(self):
        """测试默认配置（从环境变量加载）"""
        settings = Settings()
        
        # 验证基础配置（这些可能从 .env 加载）
        assert settings.deepseek_base_url == "https://api.deepseek.com/v1"
        assert settings.llm_model == "deepseek-chat"
        assert settings.embedding_model == "BAAI/bge-large-zh-v1.5"
        assert settings.embedding_device == "cpu"
        # API key 应该从环境变量加载，不应为空
        assert settings.deepseek_api_key is not None
    
    def test_cors_origins_default(self):
        """测试 CORS 默认来源"""
        settings = Settings()
        
        assert isinstance(settings.cors_origins, list)
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins
    
    def test_document_config_defaults(self):
        """测试文档配置默认值"""
        settings = Settings()
        
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 50
        assert ".pdf" in settings.allowed_extensions
        assert ".docx" in settings.allowed_extensions
        assert ".txt" in settings.allowed_extensions
        assert settings.max_file_size == 50 * 1024 * 1024
    
    def test_rag_config_defaults(self):
        """测试 RAG 配置默认值"""
        settings = Settings()
        
        assert settings.retrieval_top_k == 5
        assert settings.temperature == 0.0
        assert settings.max_tokens == 2000
    
    def test_server_config_defaults(self):
        """测试服务配置默认值"""
        settings = Settings()
        
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.log_level == "INFO"
    
    def test_data_dir_property(self):
        """测试数据目录属性"""
        settings = Settings()
        data_dir = settings.data_dir
        
        assert isinstance(data_dir, Path)
        assert str(data_dir).endswith("data")
    
    def test_chroma_path_property(self):
        """测试 Chroma 路径属性"""
        settings = Settings()
        chroma_path = settings.chroma_path
        
        assert isinstance(chroma_path, Path)
        assert chroma_path.name == "chroma_db"
    
    def test_redis_config_defaults(self):
        """测试 Redis 配置默认值"""
        settings = Settings()
        
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.redis_enabled is False


class TestGetSettings:
    """get_settings 函数测试"""
    
    def test_get_settings_returns_settings(self):
        """测试 get_settings 返回 Settings 实例"""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_settings_singleton(self):
        """测试 get_settings 返回单例"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSettingsCustomValues:
    """自定义配置值测试"""
    
    def test_custom_chunk_size(self):
        """测试自定义分块大小"""
        settings = Settings(chunk_size=1000)
        assert settings.chunk_size == 1000
    
    def test_custom_temperature(self):
        """测试自定义温度参数"""
        settings = Settings(temperature=0.7)
        assert settings.temperature == 0.7
    
    def test_custom_port(self):
        """测试自定义端口"""
        settings = Settings(port=8888)
        assert settings.port == 8888
    
    def test_custom_allowed_extensions(self):
        """测试自定义允许的扩展名"""
        settings = Settings(allowed_extensions=[".pdf", ".txt"])
        assert settings.allowed_extensions == [".pdf", ".txt"]
