from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class NewsItem(BaseModel):
    """新闻项模型"""
    title: str
    link: str
    guid: Optional[str] = None
    description: str = ""
    published_date: datetime
    source: str
    image_url: Optional[str] = None
    author: Optional[str] = None
    categories: List[str] = []
    keywords: List[str] = []
    publisher: Optional[str] = None
    subject: Optional[str] = None
    feed_id: Optional[str] = None  # 添加feed_id属性

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class NewsResponse(BaseModel):
    """新闻响应模型"""
    items: List[NewsItem]
    count: int

    class Config:
        from_attributes = True  # Changed from orm_mode = True
