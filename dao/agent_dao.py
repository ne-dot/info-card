from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.models import Agent
from utils.logger import setup_logger
import time
import uuid

logger = setup_logger('agent_dao')

class AgentDAO:
    def __init__(self, db):
        self.db = db
    
    def create_agent(self, name: str, type: str, model: str, 
                    prompt_en: str, prompt_zh: str, 
                    description: Optional[str] = None,
                    tools: Optional[str] = None) -> Agent:
        """创建一个新的Agent"""
        session = self.db.get_session()
        try:
            agent = Agent(
                key_id=str(uuid.uuid4()),
                name=name,
                type=type,
                description=description,
                prompt_en=prompt_en,
                prompt_zh=prompt_zh,
                model=model,
                tools=tools,
                create_date=int(time.time()),
                update_date=int(time.time())
            )
            session.add(agent)
            session.commit()
            logger.info(f"成功创建Agent: {name}, 类型: {type}")
            return agent
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
            agents = session.query(Agent).filter(Agent.type == type).all()
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
        """删除Agent"""
        session = self.db.get_session()
        try:
            agent = session.query(Agent).filter(Agent.key_id == key_id).first()
            if not agent:
                logger.warning(f"找不到key_id为{key_id}的Agent")
                return False
            
            session.delete(agent)
            session.commit()
            logger.info(f"成功删除Agent: {agent.name}")
            return True
        except Exception as e:
            logger.error(f"删除Agent失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()