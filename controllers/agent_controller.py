from fastapi import APIRouter, Depends, HTTPException, Request
from dao.agent_dao import AgentDAO
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user  # 导入依赖项
from models.user import UserResponse
import json
from database.agent import Agent
from config.prompts.search_prompts import SEARCH_PROMPT_EN, SEARCH_PROMPT_ZH
import uuid
import time
from sqlalchemy.orm import Session
from models.agent import AgentCreateRequest, AgentConfigRequest  # 导入新的请求模型

logger = setup_logger('agent_controller')
router = APIRouter(tags=["Agent"], include_in_schema=True)

# 全局变量存储服务实例
agent_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_dao
    agent_dao = AgentDAO(db)
    logger.info("Agent控制器初始化完成")

@router.post("/agents/create")
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

# 删除 trigger_news_agent 函数

@router.get("/agents/visibility/options")
async def get_visibility_options(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取Agent可见性选项"""
    try:
        # 从Agent类获取可见性选项
        visibility_options = Agent.get_visibility_options()
        
        # 返回结果
        return success_response({
            "options": visibility_options
        })
    except Exception as e:
        logger.error(f"获取Agent可见性选项失败: {str(e)}")
        return error_response(f"获取Agent可见性选项失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.get("/agents/status/options")
async def get_status_options(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取Agent状态选项"""
    try:
        # 从Agent类获取状态选项
        status_options = Agent.get_status_options()
        
        # 返回结果
        return success_response({
            "options": status_options
        })
    except Exception as e:
        logger.error(f"获取Agent状态选项失败: {str(e)}")
        return error_response(f"获取Agent状态选项失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    agent_data: AgentCreateRequest,  # 复用创建Agent的请求模型
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新Agent信息"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 调用服务更新Agent
        result = await agent_service.update_agent(agent_id, agent_data, current_user.user_id)
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"更新Agent失败: {str(e)}")
        return error_response(f"更新Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.post("/agents/{agent_id}/config")
async def config_agent(
    agent_id: str,
    config_data: AgentConfigRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """配置Agent的提示词、工具、模型等参数"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 调用服务配置Agent
        result = await agent_service.config_agent(
            agent_id, 
            config_data, 
            current_user.user_id
        )
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"配置Agent失败: {str(e)}")
        return error_response(f"配置Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


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
        
        # 获取总数和数据列表
        agents = result.get("agents", [])
        total = result.get("total", 0)
        
        # 构建标准化的返回结果
        response_data = {
            "agents": agents,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
        
        # 返回结果
        return success_response(response_data)
    except Exception as e:
        logger.error(f"获取所有Agent失败: {str(e)}")
        return error_response(f"获取所有Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.post("/agents/{agent_id}/trigger")
async def trigger_agent(
    agent_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """触发指定的Agent，获取AI响应"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        
        # 从请求体中获取query参数
        body = await request.json()
        query = body.get('query', None)

        # 调用服务触发Agent，传递query参数
        result = await agent_service.trigger_agent(agent_id, current_user.user_id, lang, query)
        
        logger.info(f"Agent触发成功，结果: {result}")
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"触发Agent失败: {str(e)}")
        return error_response(f"触发Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/agents/{agent_id}/tools")
async def get_agent_tools(
    agent_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取指定Agent的工具列表
    
    Args:
        agent_id: Agent ID
        
    Returns:
        工具列表
    """
    try:
        # 获取工具列表
        tools = agent_dao.get_tools_by_agent_id(agent_id)
        
        if not tools:
            return success_response({
                "tools": [],
                "message": "该Agent未配置任何工具"
            })
        
        # 转换为可序列化的字典
        tool_list = []
        for tool in tools:
            tool_dict = {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "tool_type": tool.tool_type,
                "endpoint": tool.endpoint,
                "is_enabled": tool.is_enabled,
                "config_params": tool.config_params,
                "created_at": tool.created_at,
                "updated_at": tool.updated_at
            }
            tool_list.append(tool_dict)
        
        return success_response({
            "tools": tool_list
        })
    except Exception as e:
        logger.error(f"获取Agent工具列表失败: {str(e)}")
        return error_response(f"获取Agent工具列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.get("/agents/{agent_id}/models")
async def get_agent_models(
    agent_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取指定Agent的大模型配置
    
    Args:
        agent_id: Agent ID
        
    Returns:
        模型配置
    """
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 调用服务获取Agent模型配置
        result = await agent_service.get_agent_model(agent_id)
        
        return success_response(result)
    except Exception as e:
        logger.error(f"获取Agent模型配置失败: {str(e)}")
        return error_response(f"获取Agent模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)