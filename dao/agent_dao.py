from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.agent import Agent
from database.agent_prompt import AgentPrompt
from database.agent_model_config import AgentModelConfig
from utils.logger import setup_logger
import time
import uuid
import json

logger = setup_logger('agent_dao')

class AgentDAO:
    def __init__(self, db):
        self.db = db
    
    def create_agent(self, user_id: str, name: str, type: str = "assistant", 
              description: Optional[str] = None,
              name_en: Optional[str] = None,
              name_zh: Optional[str] = None,
              pricing: Optional[float] = 0.0,
              visibility: Optional[str] = "public",
              status: Optional[str] = "published") -> Agent:
        """创建一个新的Agent"""
        session = self.db.get_session()
        try:
            # 创建Agent
            agent = Agent(
                key_id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                name_en=name_en,
                name_zh=name_zh,
                type=type,
                description=description,
                pricing=pricing,
                visibility=visibility,
                status=status,
                create_date=int(time.time()),
                update_date=int(time.time())
            )
            session.add(agent)
            session.flush()  # 获取agent.key_id
            
            # 提前获取所有需要的属性
            agent_dict = {
                'key_id': agent.key_id,
                'name': agent.name,
                'name_en': agent.name_en,
                'name_zh': agent.name_zh,
                'description': agent.description,
                'pricing': agent.pricing,
                'visibility': agent.visibility,
                'status': agent.status,
                'type': agent.type,
                'create_date': agent.create_date,
                'update_date': agent.update_date
            }
            
            session.commit()
            logger.info(f"成功创建Agent: {name}, 类型: {type}")
            
            # 重新创建一个Agent对象，避免会话关闭后的问题
            new_agent = Agent(**agent_dict)
            return new_agent
        except Exception as e:
            logger.error(f"创建Agent失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()

    
    def get_agent_by_key_id(self, key_id: str) -> Optional[Agent]:
        """通过key_id获取Agent"""
        session = self.db.get_session()
        try:
            agent = session.query(Agent).filter(Agent.key_id == key_id).first()
            return agent
        except Exception as e:
            logger.error(f"获取Agent失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_agents_by_type(self, type: str) -> List[Agent]:
        """获取指定类型的所有Agent"""
        session = self.db.get_session()
        try:
            agents = session.query(Agent).filter(
                Agent.type == type,
                Agent.is_deleted == False
            ).all()
            return agents
        except Exception as e:
            logger.error(f"获取Agent列表失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def update_agent(self, key_id: str, **kwargs) -> Optional[Agent]:
        """更新Agent信息"""
        session = self.db.get_session()
        try:
            agent = session.query(Agent).filter(Agent.key_id == key_id).first()
            if not agent:
                logger.warning(f"找不到key_id为{key_id}的Agent")
                return None
            
            # 处理提示词更新
            prompt_en = kwargs.pop('prompt_en', None)
            prompt_zh = kwargs.pop('prompt_zh', None)
            
            if prompt_en or prompt_zh:
                # 获取当前生产环境的提示词
                prompt = session.query(AgentPrompt).filter(
                    AgentPrompt.agent_id == key_id,
                    AgentPrompt.is_production == True
                ).first()
                
                if prompt:
                    # 更新现有提示词
                    if prompt_en:
                        prompt.content_en = prompt_en
                    if prompt_zh:
                        prompt.content_zh = prompt_zh
                else:
                    # 创建新提示词
                    new_prompt = AgentPrompt(
                        id=str(uuid.uuid4()),
                        agent_id=key_id,
                        version="1.0.0",
                        content_en=prompt_en or "",
                        content_zh=prompt_zh or "",
                        variables=json.dumps({}),
                        is_production=True,
                        creator_id=agent.user_id,
                        created_at=int(time.time())
                    )
                    session.add(new_prompt)
            
            # 更新提供的字段
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            
            # 更新更新时间
            agent.update_date = int(time.time())
            
            session.commit()
            logger.info(f"成功更新Agent: {agent.name}")
            return agent
        except Exception as e:
            logger.error(f"更新Agent失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_agent(self, key_id: str) -> bool:
        """软删除Agent"""
        session = self.db.get_session()
        try:
            agent = session.query(Agent).filter(Agent.key_id == key_id).first()
            if not agent:
                logger.warning(f"找不到key_id为{key_id}的Agent")
                return False
            
            # 软删除
            agent.is_deleted = True
            agent.update_date = int(time.time())
            
            session.commit()
            logger.info(f"成功删除Agent: {agent.name}")
            return True
        except Exception as e:
            logger.error(f"删除Agent失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_agent_trigger_date(self, agent_id: str) -> bool:
        """
        更新Agent的最后触发时间
        
        Args:
            agent_id: Agent的key_id
            
        Returns:
            bool: 更新是否成功
        """
        try:
            session = self.db.get_session()
            with session:
                agent = session.query(Agent).filter(Agent.key_id == agent_id).first()
                if agent:
                    agent.trigger_date = int(time.time())
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"更新Agent触发时间失败: {str(e)}")
            return False
    
    def get_agent_prompt(self, agent_id: str, is_production: bool = True) -> Optional[AgentPrompt]:
        """获取Agent的提示词"""
        session = self.db.get_session()
        try:
            prompt = session.query(AgentPrompt).filter(
                AgentPrompt.agent_id == agent_id,
                AgentPrompt.is_production == is_production
            ).first()
            return prompt
        except Exception as e:
            logger.error(f"获取Agent提示词失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_agent_model_configs(self, agent_id: str) -> List[AgentModelConfig]:
        """获取Agent的模型配置"""
        session = self.db.get_session()
        try:
            configs = session.query(AgentModelConfig).filter(
                AgentModelConfig.agent_id == agent_id,
                AgentModelConfig.is_enabled == True
            ).all()
            return configs
        except Exception as e:
            logger.error(f"获取Agent模型配置失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_all_agents(self, user_id: str, page: int = 1, page_size: int = 10) -> tuple:
        """获取所有Agent，支持分页
        
        Args:
            user_id: 用户ID
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            tuple: (Agent列表, 总数)
        """
        session = self.db.get_session()
        try:
            # 基础查询
            query = session.query(Agent).filter(
                Agent.is_deleted == False
            )
            
            # 如果提供了用户ID，则只查询该用户的Agent
            if user_id:
                query = query.filter(
                    # 用户创建的或公开的
                    (Agent.user_id == user_id) | (Agent.visibility == 'public')
                )
            
            # 计算总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            agents = query.order_by(Agent.create_date.desc()).offset(offset).limit(page_size).all()
            
            return agents, total
        except Exception as e:
            logger.error(f"获取所有Agent失败: {str(e)}")
            raise e
        finally:
            session.close()