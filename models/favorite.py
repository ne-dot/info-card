from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time

class FavoriteBase(BaseModel):
    """收藏基础模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    tag_id: Optional[str] = None

class FavoriteCreate(FavoriteBase):
    """创建收藏请求模型"""
    source_type: str  # 'google' 或 'ai'

class FavoriteUpdate(FavoriteBase):
    """更新收藏请求模型"""
    pass

class Favorite(FavoriteBase):
    """收藏完整模型"""
    id: str
    user_id: str
    source_type: str
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    is_deleted: bool = False

    class Config:
        from_attributes = True

class FavoriteResponse(Favorite):
    """收藏响应模型"""
    pass 