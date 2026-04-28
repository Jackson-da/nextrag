"""认证相关的 Pydantic 模型"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class RegisterResponse(BaseModel):
    """注册响应模型"""
    message: str = Field(..., description="消息")
    user_id: str = Field(..., description="用户 ID")


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: str = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
