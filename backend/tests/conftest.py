"""测试配置和 fixtures"""
import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.config import get_settings


@pytest.fixture(scope="session")
def test_settings():
    """测试配置"""
    return get_settings()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI 测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_text() -> str:
    """测试用文本"""
    return "这是一段测试文本。用于测试文本分割功能。我们需要确保它能正确处理各种边界情况。"
