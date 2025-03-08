from pydantic import BaseModel
from typing import Optional
import time

class SearchResult(BaseModel):
    key_id: str
    title: str
    content: str
    snippet: Optional[str] = None
    link: Optional[str] = None
    source: Optional[str] = None
    type: Optional[str] = None
    thumbnail_link: Optional[str] = None
    context_link: Optional[str] = None
    date: int = int(time.time())  # 使用时间戳

    @classmethod
    def from_gpt_response(cls, content):
        """从GPT响应创建搜索结果"""
        import uuid
        
        # 生成一个唯一ID作为key_id
        key_id = str(uuid.uuid4())
        
        return cls(
            key_id=key_id,  # 添加key_id字段
            title="AI 总结",
            content=content,
            source="gpt",
            type="text",
            date=int(time.time())
        )
    
    @classmethod
    def from_google_result(cls, result):
        """从Google搜索结果创建搜索结果"""
        import uuid
        
        # 生成一个唯一ID作为key_id
        key_id = str(uuid.uuid4())
        
        # 确保有content字段，可以使用snippet或其他字段作为备选
        content = result.get('snippet', '')
        if not content and 'title' in result:
            content = result.get('title', '')  # 如果没有snippet，使用title作为content
        
        return cls(
            key_id=key_id,  # 添加key_id字段
            title=result.get('title', '未知标题'),
            snippet=result.get('snippet', ''),
            link=result.get('link', ''),
            content=content,  # 确保有content字段
            context_link=result.get('contextLink', result.get('link', '')),
            thumbnail_link=result.get('thumbnailLink', None),
            source="google_image" if 'thumbnailLink' in result else "google",
            type="image" if 'thumbnailLink' in result else "text",
            date=int(time.time())
        )
