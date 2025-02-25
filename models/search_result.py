from dataclasses import dataclass
from typing import Optional
import uuid
from datetime import datetime

@dataclass
class SearchResult:
    id: str
    content: Optional[str]
    title: str
    snippet: Optional[str]
    link: Optional[str]
    date: str
    
    @classmethod
    def from_gpt_response(cls, content: str):
        """从 GPT 响应创建结果"""
        return cls(
            id=str(uuid.uuid4()),
            content=content,
            title="AI 生成的回答摘要",
            snippet=None,
            link=None,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    @classmethod
    def from_google_result(cls, result: dict):
        """从 Google 搜索结果创建"""
        return cls(
            id=str(uuid.uuid4()),
            content=None,
            title=result.get('title', ''),
            snippet=result.get('snippet', ''),
            link=result.get('link', ''),
            date=result.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )