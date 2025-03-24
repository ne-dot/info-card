from fastapi import APIRouter, Depends, HTTPException, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from dao.agent_prompt_dao import AgentPromptDAO

logger = setup_logger('agent_prompt_controller')
router = APIRouter(tags=["AgentPrompt"], include_in_schema=True)

# 全局变量存储DAO实例
agent_prompt_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_prompt_dao
    agent_prompt_dao = AgentPromptDAO(db)
    logger.info("AgentPrompt控制器初始化完成")

@router.get("/agents/{agent_id}/prompts")
async def get_agent_prompts(
    agent_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取指定Agent的提示词
    
    Args:
        agent_id: Agent ID
        
    Returns:
        提示词列表
    """
    try:
        # 获取提示词
        prompts = agent_prompt_dao.get_prompts_by_agent_id(agent_id)
        
        if not prompts:
            return success_response({
                "prompts": [],
                "message": "未找到该Agent的提示词"
            })
        
        # 转换为可序列化的字典
        prompt_list = []
        for prompt in prompts:
            prompt_dict = {
                "id": prompt.id,
                "agent_id": prompt.agent_id,
                "version": prompt.version,
                "content_en": prompt.content_en,
                "content_zh": prompt.content_zh,
                "variables": prompt.variables,
                "is_production": prompt.is_production,
                "creator_id": prompt.creator_id,
                "created_at": prompt.created_at
            }
            prompt_list.append(prompt_dict)
        
        return success_response({
            "prompts": prompt_list
        })
    except Exception as e:
        logger.error(f"获取Agent提示词失败: {str(e)}")
        return error_response(f"获取Agent提示词失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)