from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.chat_service import ChatService
from tools.google_search import search_google_by_text  

router = APIRouter()
chat_service = None

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    gpt_summary: dict
    google_results: List[dict]

def init_controller(service: ChatService):
    global chat_service
    chat_service = service

@router.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    try:
        results = await chat_service.search_and_respond(query.query)
        
        # 分离 GPT 和 Google 结果
        gpt_result = next(r for r in results if r.content is not None)
        google_results = [r for r in results if r.content is None]
        
        return SearchResponse(
            gpt_summary={
                "title": gpt_result.title,
                "content": gpt_result.content,
                "date": gpt_result.date
            },
            google_results=[{
                "title": r.title,
                "snippet": r.snippet,
                "link": r.link,
                "date": r.date
            } for r in google_results]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))