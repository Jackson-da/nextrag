"""安全模块 - JWT Token 和密码加密工具"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import get_settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # bcrypt 限制密码最长72字节
    return pwd_context.verify(plain_password[:72], hashed_password)


def hash_password(password: str) -> str:
    """哈希密码"""
    # bcrypt 限制密码最长72字节
    return pwd_context.hash(password[:72])


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT Access Token
    
    Args:
        data: 需要编码的数据，包含 sub (用户ID)
        expires_delta: 过期时间，默认 7 天
    
    Returns:
        JWT Token 字符串
    """
    settings = get_settings()
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    解码 JWT Token
    
    Args:
        token: JWT Token 字符串
    
    Returns:
        解码后的数据，失败返回 None
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token 已过期
        return None
    except jwt.InvalidTokenError:
        # 无效的 Token
        return None
