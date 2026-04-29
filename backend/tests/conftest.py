"""Pytest 配置文件"""
import os
from pathlib import Path
from typing import Generator
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# 设置测试环境
os.environ["ENVIRONMENT"] = "development"  # 使用 development 而不是 test

from app.models.database import Base, engine as original_engine


# 创建内存 SQLite 数据库用于测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 导入所有模型以确保它们被注册到 Base
from app.models.user import UserModel
from app.models.database import DocumentModel, KnowledgeBaseModel
from app.models.chat import ChatSessionModel, ChatMessageModel


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 测试后删除所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> UserModel:
    """创建测试用户"""
    from app.core.security import hash_password
    
    user = UserModel(
        id=str(uuid.uuid4()),
        username="testuser",
        password_hash=hash_password("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: UserModel) -> dict:
    """获取认证请求头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def client(db_session: Session, test_user: UserModel) -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    from app.main import app
    from app.models.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
