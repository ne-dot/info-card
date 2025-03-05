from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.chat_service import ChatService
from tools.google_search import search_google_by_text  

# 添加标记，表示这个路由不需要认证
router = APIRouter(tags=["搜索"], include_in_schema=True)
chat_service = None

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    gpt_summary: dict
    google_results: List[dict]

def init_controller(service: ChatService):
    global chat_service
    chat_service = service

# 保持原有路由不变
@router.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    try:
        results = await chat_service.search_and_respond(query.query)
        
        # 分离 GPT 和 Google 结果
        gpt_result = next(r for r in results if r.source is "gpt")
        google_results = [r for r in results if r.source is "google_image"]
        
        return SearchResponse(
            gpt_summary={
                "id": str(gpt_result.key_id),
                "title": gpt_result.title,
                "content": gpt_result.content,
                "date": gpt_result.date
            },
            google_results=[{
                "id": str(r.key_id),
                "title": r.title,
                "snippet": r.snippet,
                "link": r.link,
                "content_link": getattr(r, 'context_link', r.link),  # 添加content_link字段
                "thumbnailLink": getattr(r, 'thumbnail_link', None),
                "type": getattr(r, 'type', 'text'),
                "date": r.date
            } for r in google_results]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))