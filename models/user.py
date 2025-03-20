import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import time

# 在用户模型中添加 is_anonymous 字段
class User(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    password_hash: str
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    last_login: Optional[int] = None
    is_active: bool = True
    is_anonymous: bool = False
    

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username_or_email: str  # 修改为用户名或邮箱
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None  # 修改为可选，因为匿名用户没有邮箱
    created_at: int  # 使用时间戳
    last_login: Optional[int] = None  # 使用时间戳
    is_anonymous: bool = False  # 添加匿名用户标记

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class AdminLoginRequest(BaseModel):
    """管理员登录请求模型"""
    email: str
    password: str