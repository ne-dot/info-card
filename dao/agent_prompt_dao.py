from sqlalchemy.orm import Session
from database.agent_prompt import AgentPrompt
from typing import List, Optional
import uuid  # 添加uuid模块导入
import json  # 添加json模块导入

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
        ).first()
    
    def create_prompt(self, agent_id: str, creator_id: str, 
                     content_zh: str = None, content_en: str = None, 
                     version: str = "1.0.0", variables: str = None, 
                     is_production: bool = False) -> AgentPrompt:
        """创建提示词
        
        Args:
            agent_id: Agent ID
            creator_id: 创建者ID
            content_zh: 中文提示词内容
            content_en: 英文提示词内容
            version: 版本号，默认为1.0.0
            variables: 可注入变量配置，JSON格式
            is_production: 是否生产环境，默认为False
        
        Returns:
            AgentPrompt: 创建的提示词对象
        """
        prompt = AgentPrompt(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            creator_id=creator_id,
            content_zh=content_zh,
            content_en=content_en,
            version=version,
            variables=variables if variables else json.dumps({}),
            is_production=is_production
        )
        
        self.session.add(prompt)
        self.session.flush()
        
        return prompt
    
    def update_prompt(self, prompt_id: str, content_zh: str = None, 
                     content_en: str = None, version: str = None,
                     variables: str = None, is_production: bool = None) -> Optional[AgentPrompt]:
        """更新提示词
        
        Args:
            prompt_id: 提示词ID
            content_zh: 中文提示词内容
            content_en: 英文提示词内容
            version: 版本号
            variables: 可注入变量配置，JSON格式
            is_production: 是否生产环境
            
        Returns:
            Optional[AgentPrompt]: 更新后的提示词对象，如果不存在则返回None
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None
            
        if content_zh is not None:
            prompt.content_zh = content_zh
        if content_en is not None:
            prompt.content_en = content_en
        if version is not None:
            prompt.version = version
        if variables is not None:
            prompt.variables = variables
        if is_production is not None:
            prompt.is_production = is_production
            
        self.session.flush()
        
        return prompt
    
    
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
            AgentPrompt.language == language
        ).first()
        
        # 如果没有找到，返回任意语言的第一个提示词
        if not prompt:
            prompt = self.session.query(AgentPrompt).filter(
                AgentPrompt.agent_id == agent_id
            ).first()
            
        return prompt