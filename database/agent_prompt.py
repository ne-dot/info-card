from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
import time
import uuid
import json
from .base import Base

# Agent提示词版本表
class AgentPrompt(Base):
    """Agent提示词版本表"""
    __tablename__ = "agent_prompts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.key_id"), nullable=False)
    version = Column(String(20), nullable=False, default="1.0.0", comment='版本号')
    content_en = Column(Text, nullable=True, comment='英文prompt模板内容')
    content_zh = Column(Text, nullable=True, comment='中文prompt模板内容')
    variables = Column(Text, comment='可注入变量配置，JSON格式')
    is_production = Column(Boolean, default=False, comment='是否生产环境')
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False, comment='修改者ID')
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间')
    
    # 关系
    agent = relationship("Agent", back_populates="prompts")
    creator = relationship("UserModel")
    
    @classmethod
    def init_default_prompts(cls, session, agent_id, creator_id, prompt_type="search"):
        """初始化默认提示词"""
        from config.prompts.news_prompts import BASE_PROMPT_ZH, BASE_PROMPT_EN
        from config.prompts.search_prompts import SEARCH_PROMPT_ZH, SEARCH_PROMPT_EN
        
        prompts = []
        
        if prompt_type == "search":
            # 搜索总结提示词
            search_prompt = cls(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                version="1.0.0",
                content_zh=SEARCH_PROMPT_ZH,
                content_en=SEARCH_PROMPT_EN,
                variables=json.dumps({"query": "", "search_results": []}),
                is_production=True,
                creator_id=creator_id
            )
            prompts.append(search_prompt)
            
        elif prompt_type == "news":
            # 新闻总结提示词
            news_prompt = cls(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                version="1.0.0",
                content_zh=BASE_PROMPT_ZH,
                content_en=BASE_PROMPT_EN,
                variables=json.dumps({"news_text": ""}),
                is_production=True,
                creator_id=creator_id
            )
            prompts.append(news_prompt)
        
        # 添加到会话
        for prompt in prompts:
            session.add(prompt)
        
        return prompts