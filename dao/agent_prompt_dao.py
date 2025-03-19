from sqlalchemy.orm import Session
from database.agent_prompt import AgentPrompt
from typing import List, Optional

class AgentPromptDAO:
    """Agent提示词数据访问对象"""
    
    def __init__(self, db):
        self.db = db
        self.session = db.get_session()
    
    def get_prompts_by_agent_id(self, agent_id: str):
        """获取指定Agent的所有提示词
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List[AgentPrompt]: 提示词列表
        """
        session = self.db.get_session()
        try:
            # 移除对is_deleted的过滤，并打印返回的提示词属性以便调试
            prompts = session.query(AgentPrompt).filter(
                AgentPrompt.agent_id == agent_id
            ).all()
            
            # 调试信息
            if prompts:
                from utils.logger import setup_logger
                logger = setup_logger('agent_prompt_dao')
                logger.info(f"获取到提示词，第一个提示词属性: {dir(prompts[0])}")
                
            return prompts
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('agent_prompt_dao')
            logger.error(f"获取Agent提示词失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[AgentPrompt]:
        """根据ID获取提示词
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            Optional[AgentPrompt]: 提示词对象，如果不存在则返回None
        """
        return self.session.query(AgentPrompt).filter(
            AgentPrompt.id == prompt_id,
            AgentPrompt.is_deleted == False
        ).first()
    
    def create_prompt(self, agent_id: str, content: str, name: str, 
                     language: str = 'en', user_id: str = None) -> AgentPrompt:
        """创建提示词
        
        Args:
            agent_id: Agent ID
            content: 提示词内容
            name: 提示词名称
            language: 语言，默认为英文
            user_id: 创建者ID
            
        Returns:
            AgentPrompt: 创建的提示词对象
        """
        prompt = AgentPrompt(
            agent_id=agent_id,
            content=content,
            name=name,
            language=language,
            user_id=user_id
        )
        
        self.session.add(prompt)
        self.session.flush()
        
        return prompt
    
    def update_prompt(self, prompt_id: str, content: str = None, 
                     name: str = None, language: str = None) -> Optional[AgentPrompt]:
        """更新提示词
        
        Args:
            prompt_id: 提示词ID
            content: 提示词内容
            name: 提示词名称
            language: 语言
            
        Returns:
            Optional[AgentPrompt]: 更新后的提示词对象，如果不存在则返回None
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None
            
        if content is not None:
            prompt.content = content
        if name is not None:
            prompt.name = name
        if language is not None:
            prompt.language = language
            
        self.session.flush()
        
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """删除提示词（软删除）
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            bool: 是否成功删除
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return False
            
        prompt.is_deleted = True
        self.session.flush()
        
        return True
    
    def get_default_prompt(self, agent_id: str, language: str = 'en') -> Optional[AgentPrompt]:
        """获取Agent的默认提示词
        
        Args:
            agent_id: Agent ID
            language: 语言，默认为英文
            
        Returns:
            Optional[AgentPrompt]: 默认提示词对象，如果不存在则返回None
        """
        # 先尝试获取指定语言的提示词
        prompt = self.session.query(AgentPrompt).filter(
            AgentPrompt.agent_id == agent_id,
            AgentPrompt.language == language,
            AgentPrompt.is_deleted == False
        ).first()
        
        # 如果没有找到，返回任意语言的第一个提示词
        if not prompt:
            prompt = self.session.query(AgentPrompt).filter(
                AgentPrompt.agent_id == agent_id,
                AgentPrompt.is_deleted == False
            ).first()
            
        return prompt