from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator
from typing import List, Optional
import json
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
        
        # 创建一个异步生成器来处理流式响应
        async def sse_generator():
            google_results = []
            
            # 发送初始事件
            yield f"data: {json.dumps({'event': 'start', 'data': {'query': query.query}})}\n\n"
            
            try:
                # 触发这个agent，传递query参数，但不启用流式响应
                result = await agent_service.trigger_agent(
                    agent_id=agent.key_id, 
                    user_id=user_id, 
                    lang=lang, 
                    query=query.query,
                    stream=False  # 暂时使用非流式响应
                )
                
                # 检查结果
                if not result or "error" in result:
                    error_msg = result.get("error", "搜索失败") if result else "搜索失败"
                    yield f"data: {json.dumps({'event': 'error', 'data': {'error': error_msg}})}\n\n"
                    return
                
                # 获取AI响应
                ai_response = result.get("ai_response", "")
                
                # 模拟流式返回AI响应（每个字符作为一个块）
                # 实际应用中可以按句子或段落分割
                for i in range(0, len(ai_response), 10):  # 每10个字符一个块
                    chunk = ai_response[i:i+10]
                    yield f"data: {json.dumps({'event': 'chunk', 'data': {'content': chunk}})}\n\n"
                    # 可以添加一个小延迟来模拟真实的流式效果
                    # await asyncio.sleep(0.05)
                
                # 获取Google搜索结果
                if "tool_results" in result and isinstance(result["tool_results"], dict):
                    tool_results = result["tool_results"]
                    if "google_search" in tool_results and isinstance(tool_results["google_search"], dict):
                        google_search = tool_results["google_search"]
                        if "image_results" in google_search and isinstance(google_search["image_results"], list):
                            google_results = google_search["image_results"]
                
                # 发送Google搜索结果
                yield f"data: {json.dumps({'event': 'google_results', 'data': {'results': google_results}})}\n\n"
                
                # 发送结束事件
                yield f"data: {json.dumps({'event': 'end', 'data': {'invocation_id': result.get('invocation_id', ''), 'full_response': ai_response}})}\n\n"
            
            except Exception as e:
                logger.error(f"流式处理过程中出错: {str(e)}")
                yield f"data: {json.dumps({'event': 'error', 'data': {'error': str(e)}})}\n\n"
        
        # 返回流式响应
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
            }
        )
    
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        # 对于流式响应的错误，返回一个流式错误响应
        async def error_generator():
            yield f"data: {json.dumps({'event': 'error', 'data': {'error': str(e)}})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )
