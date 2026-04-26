"""依赖注入容器 - 解耦服务层依赖"""
from app.config import Settings, get_settings


class Container:
    """
    依赖注入容器
    
    提供统一的服务实例管理，支持依赖注入和测试 Mock。
    遵循单一职责原则，所有服务实例通过此容器获取。
    """
    
    def __init__(self):
        self._settings: Settings | None = None
        self._chat_service = None
        self._document_service = None
        self._vectorstore = None
        self._embeddings = None
    
    @property
    def settings(self) -> Settings:
        """获取配置"""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    def reset(self):
        """重置所有服务实例（用于测试或配置变更）"""
        self._chat_service = None
        self._document_service = None
        self._vectorstore = None
        self._embeddings = None


# 全局容器实例
_container: Container | None = None


def get_container() -> Container:
    """获取依赖注入容器"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container():
    """重置容器（用于测试）"""
    global _container
    if _container is not None:
        _container.reset()


# ==================== 服务懒加载函数 ====================

def get_settings() -> Settings:
    """获取配置（向后兼容）"""
    return get_container().settings


def get_chat_service():
    """获取聊天服务（向后兼容）"""
    from app.services.chat_service import get_chat_service as _get_chat_service
    return _get_chat_service()


def get_document_service():
    """获取文档服务（向后兼容）"""
    from app.services.document_service import get_document_service as _get_document_service
    return _get_document_service()
