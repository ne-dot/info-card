from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, validator
from typing import List, Optional
from services.search_service import SearchService
from tools.google_search import search_google_by_text  
from utils.response_utils import success_response, error_response, ErrorCode
from utils.logger import setup_logger
from utils.jwt_utils import decode_token  # 导入解析token的函数
from models.user import User
import re

# 初始化日志记录器
logger = setup_logger('search_controller')

# 添加标记，表示这个路由不需要认证
router = APIRouter(tags=["搜索"], include_in_schema=True)
search_service = None

class SearchQuery(BaseModel):
    query: str
    
    @validator('query')
    def validate_query(cls, v):
        # 检查是否为GraphQL查询
        if re.search(r'(query\s+\w+|__schema|__type|__typename)', v, re.IGNORECASE):
            raise ValueError("不支持的查询类型")
        
        # 检查查询长度
        if len(v.strip()) < 2:
            raise ValueError("查询内容太短")
        
        if len(v) > 500:
            raise ValueError("查询内容过长")
            
        return v

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
                user_id = anonymous_id
                # 继续执行，不返回错误，因为搜索不需要强制认证
                # 此时会使用请求头中的匿名ID（如果有）
        else:
            # 如果没有token，使用匿名ID
            user_id = anonymous_id

        logger.info(f"用户ID: {user_id}")
        logger.info(f"匿名ID: {anonymous_id}")  
        # 检查user_id是否存在，如果不存在则返回错误
        if not user_id:
            return error_response("未提供有效的用户ID", ErrorCode.UNAUTHORIZED)
            
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 获取语言设置
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        
        # 从agent表中查询name=AI搜索的agent
        agent = agent_service.agent_dao.get_agent_by_name("AI搜索")
        if not agent:
            return error_response("未找到AI搜索Agent", ErrorCode.SEARCH_FAILED)
        
        # 触发这个agent，传递query参数
        result = await agent_service.trigger_agent(agent.key_id, user_id, lang, query.query)
        
        # 处理返回结果
        if not result or "error" in result:
            error_msg = result.get("error", "搜索失败") if result else "搜索失败"
            return error_response(error_msg, ErrorCode.SEARCH_FAILED)
        
        # 构建响应数据
        # 从嵌套结构中提取google_search的text_results
        google_results = []
        if "tool_results" in result and isinstance(result["tool_results"], dict):
            tool_results = result["tool_results"]
            if "google_search" in tool_results and isinstance(tool_results["google_search"], dict):
                google_search = tool_results["google_search"]
                if "image_results" in google_search and isinstance(google_search["image_results"], list):
                    google_results = google_search["image_results"]
        
        search_results_dict = {
            "gpt_summary": result.get("ai_response", {}),
            "google_results": google_results
        }

        return success_response(search_results_dict)
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return error_response(f"搜索失败: {str(e)}", ErrorCode.SEARCH_FAILED)
