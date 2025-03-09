from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
from services.search_service import SearchService
from tools.google_search import search_google_by_text  
from utils.response_utils import success_response, error_response, ErrorCode
from utils.logger import setup_logger

# 初始化日志记录器
logger = setup_logger('search_controller')

# 添加标记，表示这个路由不需要认证
router = APIRouter(tags=["搜索"], include_in_schema=True)
search_service = None

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    gpt_summary: dict
    google_results: List[dict]

def init_controller(service: SearchService):
    global search_service
    search_service = service

@router.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery, request: Request):
    try:
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        results = await search_service.search_and_respond(query.query, lang)
        
        # 分离 GPT 和 Google 结果
        gpt_result = next((r for r in results if r.source == "gpt"), None)  # 使用 == 而不是 is
        google_results = [r for r in results if r.source == "google_image"]  # 使用 == 而不是 is
        
        if not gpt_result:
            return error_response("未找到GPT结果", ErrorCode.SEARCH_FAILED)
        
        # 创建响应数据字典，而不是直接使用 SearchResponse 对象
        search_results_dict = {
            "gpt_summary": {
                "id": str(gpt_result.key_id),
                "title": gpt_result.title,
                "content": gpt_result.content,
                "date": gpt_result.date
            },
            "google_results": [{
                "id": str(r.key_id),
                "title": r.title,
                "snippet": r.snippet,
                "link": r.link,
                "content_link": getattr(r, 'context_link', r.link),
                "thumbnailLink": getattr(r, 'thumbnail_link', None),
                "type": getattr(r, 'type', 'text'),
                "date": r.date
            } for r in google_results]
        }

        return success_response(search_results_dict)
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return error_response(f"搜索失败: {str(e)}", ErrorCode.SEARCH_FAILED)