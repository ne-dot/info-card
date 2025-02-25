from dataclasses import dataclass
from typing import Optional
import uuid
from datetime import datetime

@dataclass
class SearchResult:
    def __init__(
        self,
        id: Optional[int] = None,
        key_id: Optional[str] = None,
        query: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        snippet: Optional[str] = None,
        link: Optional[str] = None,
        date: Optional[datetime] = None,
        source: Optional[str] = None
    ):
        self.id = id
        self.key_id = key_id or str(uuid.uuid4())
        self.query = query
        self.title = title
        self.content = content
        self.snippet = snippet
        self.link = link
        self.date = date or datetime.now()
        self.source = source
    
    @classmethod
    def from_gpt_response(cls, content: str, query: str = None):
        return cls(
            key_id=str(uuid.uuid4()),
            query=query,
            content=content,
            title="AI 生成的回答摘要",
            source="gpt",
        )
    
    @classmethod
    def from_google_result(cls, result: dict, query: str = None):
        return cls(
            key_id=str(uuid.uuid4()),
            query=query,
            content=None,
            title=result.get('title', ''),
            snippet=result.get('snippet', ''),
            link=result.get('link', ''),
            source="google"
        )