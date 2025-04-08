from pydantic import BaseModel, Field
from typing import Optional, List
import time

class TagBase(BaseModel):
    """标签基础模型"""
    name: str
    description: Optional[str] = None

class TagCreate(TagBase):
    """创建标签请求模型"""
    user_id: str

class TagUpdate(TagBase):
    """更新标签请求模型"""
    pass

class Tag(TagBase):
    """标签完整模型"""
    id: str
    user_id: str
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    is_deleted: bool = False

    class Config:
        from_attributes = True

class TagResponse(Tag):
    """标签响应模型"""
    pass

class TagListResponse(BaseModel):
    """标签列表响应模型"""
    tags: List[TagResponse]
    total: int 