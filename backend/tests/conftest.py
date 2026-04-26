"""测试配置和 fixtures"""
import sys
import os
from pathlib import Path
from typing import Generator
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.config import get_settings
from app.models.database import Base


# 创建内存数据库用于测试 - 使用 StaticPool 确保所有连接共享同一数据库
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_settings():
    """测试配置"""
    return get_settings()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """创建测试数据库表"""
    # 创建测试数据库表
    Base.metadata.create_all(bind=test_engine)
    yield
    # 测试结束后清理
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """FastAPI 测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """数据库会话 - 使用内存数据库，每次测试后回滚"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_text() -> str:
    """测试用文本"""
    return "这是一段测试文本。用于测试文本分割功能。我们需要确保它能正确处理各种边界情况。"
