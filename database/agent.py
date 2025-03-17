from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, Integer, Float
from sqlalchemy.orm import relationship
import time
import uuid
import json
from .base import Base
from .agent_model_config import AgentModelConfig
from .agent_prompt import AgentPrompt

class Agent(Base):
    """Agent 模型，用于存储智能代理配置"""
    __tablename__ = "agents"
    
    # 使用key_id作为主键，不再使用自增id
    key_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, comment='创建者ID')
    name = Column(String(100), nullable=False)  # 默认名称
    name_en = Column(String(100), nullable=True)  # 英文名称
    name_zh = Column(String(100), nullable=True)  # 中文名称
    description = Column(Text, nullable=True)  # Agent的详细描述
    
    # 基础配置
    model = Column(String(100), nullable=False, comment='使用的基础模型，如 gpt-4, deepseek 等')
    temperature = Column(Float, default=0.7, comment='温度参数')
    max_tokens = Column(Integer, default=1000, comment='最大token数')
    
    # 业务属性
    pricing = Column(Float, default=0.0, comment='单价/月')
    visibility = Column(Enum('public', 'private', 'organization', name='visibility_enum'), 
                        default='public', comment='可见性')
    status = Column(Enum('draft', 'published', 'archived', name='status_enum'), 
                   default='draft', comment='状态')
    
    # 类型
    type = Column(Enum('assistant', 'search', 'expert', 'technews', name='agent_type_enum'), 
                 nullable=False, default="assistant", comment="agent类型")
    
    # 工具配置
    tools = Column(Text, nullable=True, comment='存储工具配置，可以是JSON格式')
    
    # 审计字段
    create_date = Column(Integer, default=lambda: int(time.time()), comment='创建时间')
    update_date = Column(Integer, default=lambda: int(time.time()), 
                         onupdate=lambda: int(time.time()), comment='更新时间')
    trigger_date = Column(Integer, nullable=True, comment='最后一次触发时间')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    
    # 关系
    model_configs = relationship("AgentModelConfig", back_populates="agent", cascade="all, delete-orphan")
    prompts = relationship("AgentPrompt", back_populates="agent", cascade="all, delete-orphan")
    
    # 与用户的关系
    creator = relationship("UserModel")
    
    @classmethod
    def init_default_agents(cls, session, creator_id):
        """初始化默认Agent"""
        # 创建搜索Agent
        search_agent = cls(
            key_id=str(uuid.uuid4()),
            user_id=creator_id,
            name="搜索助手",
            name_en="Search Assistant",
            name_zh="搜索助手",
            description="专业的搜索结果分析和总结助手",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            pricing=0.0,
            visibility="public",
            status="published",
            type="search",
            tools=json.dumps({"search": {"enabled": True}}),
            is_deleted=False
        )
        
        # 创建新闻Agent
        news_agent = cls(
            key_id=str(uuid.uuid4()),
            user_id=creator_id,
            name="科技新闻助手",
            name_en="Tech News Assistant",
            name_zh="科技新闻助手",
            description="专业的科技新闻分析和总结助手",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            pricing=0.0,
            visibility="public",
            status="published",
            type="technews",
            tools=json.dumps({"news_fetch": {"enabled": True}}),
            is_deleted=False
        )
        
        # 添加到会话
        session.add(search_agent)
        session.add(news_agent)
        session.flush()  # 确保ID已生成
        
        # 初始化模型配置
        AgentModelConfig.init_default_models(session, search_agent.key_id)
        AgentModelConfig.init_default_models(session, news_agent.key_id)
        
        # 初始化提示词
        AgentPrompt.init_default_prompts(session, search_agent.key_id, creator_id, "search")
        AgentPrompt.init_default_prompts(session, news_agent.key_id, creator_id, "news")
        
        return [search_agent, news_agent]