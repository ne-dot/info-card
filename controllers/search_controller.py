from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.search_service import SearchService
from tools.google_search import search_google_by_text  
from utils.response_utils import success_response, error_response, ErrorCode
from utils.logger import setup_logger
from utils.jwt_utils import decode_token  # 导入解析token的函数
from models.user import User

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
        # 从请求头中获取token
        token = request.headers.get("Authorization")
        user_id = None
        # 从请求头中获取匿名ID（如果有）
        anonymous_id = request.headers.get("X-Anonymous-ID")
        
        # 如果有token，尝试解析
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
            try:
                # 解析token获取user_id
                payload = decode_token(token)
                if payload and "sub" in payload:
                    user_id = payload["sub"]
                    # 如果成功获取了user_id，则不使用匿名ID
                    anonymous_id = None
            except Exception as e:
                logger.warning(f"解析token失败: {str(e)}")
                # 继续执行，不返回错误，因为搜索不需要强制认证
                # 此时会使用请求头中的匿名ID（如果有）
        
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        results = await search_service.search_and_respond(
            query.query, 
            lang, 
            user_id=user_id, 
            anonymous_id=anonymous_id
        )
        
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
