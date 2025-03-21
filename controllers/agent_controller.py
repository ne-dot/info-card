from fastapi import APIRouter, Depends, HTTPException, Request
from dao.agent_dao import AgentDAO
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user  # 导入依赖项
from models.user import UserResponse
import json
from database.agent import Agent
from config.prompts.search_prompts import SEARCH_PROMPT_EN, SEARCH_PROMPT_ZH
from config.prompts.news_prompts import BASE_PROMPT_EN, BASE_PROMPT_ZH
import uuid
import time
from sqlalchemy.orm import Session
from models.agent import AgentCreateRequest

logger = setup_logger('agent_controller')
router = APIRouter(tags=["Agent"], include_in_schema=True)

# 全局变量存储服务实例
agent_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_dao
    agent_dao = AgentDAO(db)
    logger.info("Agent控制器初始化完成")

@router.post("/agent/create")
async def create_agent(
    agent_data: AgentCreateRequest, 
    request: Request, 
    current_user: UserResponse = Depends(get_current_user)
):
    """创建一个新的Agent"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 调用服务创建Agent，传递用户ID
        result = await agent_service.create_agent(agent_data, current_user.user_id)
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"创建Agent失败: {str(e)}")
        return error_response(f"创建Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.post("/agents/trigger/news")
async def trigger_news_agent(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """触发科技新闻Agent，获取最新科技新闻总结"""
    try:
        # 将当前用户信息添加到请求状态中
        request.state.user = current_user
        
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 调用agent服务生成新闻总结
        result = await agent_service.generate_tech_news_summary(request, limit=10, user_id=current_user.user_id)
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"触发新闻Agent失败: {str(e)}")
        return error_response(f"触发新闻Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.get("/agents")
async def get_all_agents(
    page: int = 1, 
    page_size: int = 10,
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有Agent，支持分页"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 创建请求参数
        from models.agent import AgentListRequest
        agent_request = AgentListRequest(
            page=page,
            page_size=page_size,
            user_id=current_user.user_id
        )
        
        # 调用服务获取所有Agent
        result = await agent_service.get_all_agents(agent_request)
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"获取所有Agent失败: {str(e)}")
        return error_response(f"获取所有Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)
