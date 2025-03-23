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
    
    def remove_all_agent_tools(self, agent_id: str) -> bool:
        """删除Agent的所有工具关联
        
        Args:
            agent_id: Agent ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            # 获取会话
            session = self.db.get_session()
            
            # 获取Agent对象
            agent = session.query(Agent).filter(Agent.key_id == agent_id).first()
            if not agent:
                return False
            
            # 清空工具关联
            agent.tools = []
            
            # 提交事务
            session.commit()
            
            return True
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('agent_dao')
            logger.error(f"删除Agent工具关联失败: {str(e)}")
            
            # 回滚事务
            if 'session' in locals():
                session.rollback()
            return False
        finally:
            # 关闭会话
            if 'session' in locals():
                session.close()
    
    def add_agent_tool(self, agent_id: str, tool_id: str) -> bool:
        """为Agent添加工具关联
        
        Args:
            agent_id: Agent ID
            tool_id: 工具ID
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 获取会话
            session = self.db.get_session()
            
            # 获取Agent和Tool对象
            from database.agent import Agent
            # 修改导入语句，使用正确的Tool模型导入路径
            from database.tool_models import Tool
            
            agent = session.query(Agent).filter(Agent.key_id == agent_id).first()
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            
            if not agent or not tool:
                logger.error(f"添加工具关联失败: Agent或Tool不存在 (agent_id={agent_id}, tool_id={tool_id})")
                return False
            
            # 添加工具关联
            if tool not in agent.tools:
                agent.tools.append(tool)
                logger.info(f"成功添加工具关联: Agent={agent.name}, Tool={tool.id}")
            else:
                logger.info(f"工具关联已存在: Agent={agent.name}, Tool={tool.id}")
            
            # 提交事务
            session.commit()
            
            return True
        except Exception as e:
            logger.error(f"添加Agent工具关联失败: {str(e)}")
            
            # 回滚事务
            if 'session' in locals():
                session.rollback()
            return False
        finally:
            # 关闭会话
            if 'session' in locals():
                session.close()
    
    def get_tools_by_agent_id(self, agent_id):
        """获取Agent关联的工具列表
        
        Args:
            agent_id: Agent的ID
            
        Returns:
            list: 工具对象列表
        """
        try:
            session = self.db.get_session()
            
            # 获取Agent对象
            from database.agent import Agent
            from database.tool_models import Tool
            
            # 直接通过Agent对象获取关联的工具
            agent = session.query(Agent).filter(Agent.key_id == agent_id).first()
            if not agent:
                logger.warning(f"找不到ID为{agent_id}的Agent")
                return []
            
            # 返回关联的工具列表
            return agent.tools
            
        except Exception as e:
            # 使用全局logger
            logger.error(f"获取Agent工具列表失败: {str(e)}")
            return []
        finally:
            session.close()