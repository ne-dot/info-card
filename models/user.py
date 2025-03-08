import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import time

class User:
    def __init__(self, username, email, password_hash, user_id=None, created_at=None, last_login=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or int(time.time())  # 使用时间戳
        self.last_login = last_login
        self.is_active = True

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
    email: str
    created_at: int  # 使用时间戳
    last_login: Optional[int] = None  # 使用时间戳

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None