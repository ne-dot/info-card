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
    def from_gpt_response(cls, content: str):
        return cls(
            title="AI 总结",
            content=content,
            source="gpt",
            type="text"
        )

    @classmethod
    def from_google_result(cls, result):
        if result.get('source') == 'google_image':
            return cls(
                title=result.get('title'),
                link=result.get('link'),
                snippet=result.get('snippet'),  # 添加 snippet 字段
                thumbnail_link=result.get('thumbnailLink'),
                context_link=result.get('contextLink'),
                source='google_image',
                type='image'
            )
        else:
            return cls(
                title=result.get('title'),
                snippet=result.get('snippet'),
                link=result.get('link'),
                source='google',
                type='text'
            )
