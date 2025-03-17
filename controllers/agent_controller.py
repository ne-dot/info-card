from fastapi import APIRouter, Depends, HTTPException, Request
from dao.agent_dao import AgentDAO
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
import json
from database.agent import Agent
from config.prompts.search_prompts import SEARCH_PROMPT_EN, SEARCH_PROMPT_ZH
from config.prompts.news_prompts import BASE_PROMPT_EN, BASE_PROMPT_ZH
import uuid
import time

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
async def create_agent(data: dict, request: Request):
    """创建一个新的Agent"""
    try:
        # 检查必要的参数
        required_fields = ['name', 'type', 'model', 'prompt_en', 'user_id']
        for field in required_fields:
            if field not in data:
                return error_response(f'缺少必要参数: {field}', ErrorCode.INVALID_PARAMS)
        
        # 创建Agent
        agent = agent_dao.create_agent(
            user_id=data['user_id'],
            name=data['name'],
            type=data['type'],
            model=data['model'],
            prompt_en=data['prompt_en'],
            prompt_zh=data.get('prompt_zh', ''),  # 中文提示词可选
            description=data.get('description', ''),
            name_en=data.get('name_en', ''),
            name_zh=data.get('name_zh', ''),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 1000),
            tools=json.dumps(data.get('tools', {})) if 'tools' in data else None
        )
        
        # 返回创建的Agent信息
        return success_response({
            'key_id': agent.key_id,
            'name': agent.name,
            'type': agent.type,
            'model': agent.model,
            'create_date': agent.create_date
        })
    except Exception as e:
        logger.error(f"创建Agent失败: {str(e)}")
        return error_response(f"创建Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)
