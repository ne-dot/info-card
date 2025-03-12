from fastapi import APIRouter, Depends, HTTPException, Request
from dao.agent_dao import AgentDAO
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
import json
from database.models import Agent
from config.prompts.search_prompts import summary_prompt_en, summary_prompt_cn
from config.prompts.news_prompts import get_news_summary_prompt_en, get_news_summary_prompt
from config.prompts.news_prompts import BASE_PROMPT_EN, BASE_PROMPT_ZH
import uuid
import time

logger = setup_logger('agent_controller')
router = APIRouter(tags=["Agent"], include_in_schema=True)

# 全局变量存储服务实例
agent_dao = None

# def get_agent_dao(request: Request):
#     return request.app.state.agent_dao

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_dao
    agent_dao = AgentDAO(db)
    logger.info("Agent控制器初始化完成")

@router.post("/agent/create")
async def create_agent(data: dict):
    """创建一个新的Agent"""
    try:
        # 检查必要的参数
        required_fields = ['name', 'type', 'model', 'prompt_en']
        for field in required_fields:
            if field not in data:
                return error_response(f'缺少必要参数: {field}', ErrorCode.INVALID_PARAMS)
        
        # 创建Agent
        agent = agent_dao.create_agent(
            name=data['name'],
            type=data['type'],
            model=data['model'],
            prompt_en=data['prompt_en'],
            prompt_zh=data.get('prompt_zh', ''),  # 中文提示词可选
            description=data.get('description', ''),
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

@router.post("/agent/create_search_agent")
async def create_search_agent():
    """创建一个搜索类型的Agent"""
    try:
        session = agent_dao.db.get_session()
        with session:
            agent = Agent(
                key_id=str(uuid.uuid4()),
                name="AI查询agent",
                name_zh="AI查询agent",
                name_en="AI Search Agent",
                type="search",
                model="deepseek",
                prompt_en=summary_prompt_en,
                prompt_zh=summary_prompt_cn,
                description="用于处理搜索请求并生成摘要的智能代理",
                create_date=int(time.time()),
                update_date=int(time.time())
            )
            session.add(agent)
            session.commit()
            
            # 在会话关闭前获取所有需要的数据
            agent_data = {
                'key_id': agent.key_id,
                'name': agent.name,
                'type': agent.type,
                'model': agent.model,
                'create_date': agent.create_date
            }
        
        # 会话已关闭，使用之前保存的数据
        return success_response(agent_data)
    except Exception as e:
        logger.error(f"创建搜索Agent失败: {str(e)}")
        return error_response(f"创建搜索Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)


@router.post("/agent/create_technews_agent")
async def create_technews_agent():
    """创建一个技术新闻处理的Agent"""
    try:
        session = agent_dao.db.get_session()
        with session:
            agent = Agent(
                key_id=str(uuid.uuid4()),
                name="科技新闻agent",
                name_zh="科技新闻agent",
                name_en="Tech News Agent",
                type="technews",
                model="deepseek",
                prompt_en=BASE_PROMPT_EN,
                prompt_zh=BASE_PROMPT_ZH,
                description="用于分析和总结科技新闻的智能代理",
                create_date=int(time.time()),
                update_date=int(time.time())
            )
            session.add(agent)
            session.commit()
            
            agent_data = {
                'key_id': agent.key_id,
                'name': agent.name,
                'type': agent.type,
                'model': agent.model,
                'create_date': agent.create_date
            }
        
        return success_response(agent_data)
    except Exception as e:
        logger.error(f"创建技术新闻Agent失败: {str(e)}")
        return error_response(f"创建技术新闻Agent失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)