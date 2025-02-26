from datetime import datetime
import uuid

class SearchResult:
    def __init__(self, title=None, content=None, snippet=None, link=None, source=None, 
                 type='text', thumbnail_link=None, context_link=None):
        self.key_id = uuid.uuid4()
        self.title = title
        self.content = content
        self.snippet = snippet
        self.link = link
        self.source = source
        self.type = type
        self.thumbnail_link = thumbnail_link
        self.context_link = context_link
        self.date = datetime.now()

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