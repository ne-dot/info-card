from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, Integer, Float
from sqlalchemy.orm import relationship
import time
import uuid
import json
from .base import Base
from .agent_model_config import AgentModelConfig
from .agent_prompt import AgentPrompt
# 添加 Subscription 的导入
from .subscription import Subscription
from .tool_models import agent_tool_mapping

# 移除导入中间表
# from .rss_feed import agent_feed_association

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
    model_config_id = Column(String(36), ForeignKey("agent_model_configs.id"), nullable=True)
    model_config = relationship("AgentModelConfig", back_populates="agents")
    
    prompts = relationship("AgentPrompt", back_populates="agent", cascade="all, delete-orphan")
    # 使用字符串形式的类名，延迟加载关系
    subscriptions = relationship("Subscription", back_populates="agent", cascade="all, delete-orphan", lazy="dynamic")
    invocations = relationship("AgentInvocation", back_populates="agent")
    # 添加与AgentRSSFeed的关系
    agent_feeds = relationship("AgentRSSFeed", back_populates="agent", cascade="all, delete-orphan")
    
    # 在Agent类中添加与RSSFeed的关系
    # 移除直接的多对多关系
    # feeds = relationship("RSSFeed", secondary=agent_feed_association, back_populates="agents")
      # 与 Tool 的多对多关系
    tools = relationship("Tool", secondary="agent_tool_mapping", back_populates="agents")
    # 与用户的关系
    creator = relationship("UserModel")
    
    def requires_subscription(self):
        """判断该Agent是否需要订阅
        
        Returns:
            bool: 如果是search类型返回False，其他类型返回True
        """
        return self.type != "search"
    
    def check_user_access(self, user_id):
        """检查用户是否有权限访问该Agent
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 用户是否有权限访问
        """
        # search类型的agent不需要订阅，直接返回True
        if self.type == "search":
            return True
            
        # 创建者可以访问自己创建的agent
        if self.user_id == user_id:
            return True
            
        # 检查用户是否有有效订阅
        # 由于使用了lazy="dynamic"，需要调用all()方法获取所有订阅
        for subscription in self.subscriptions.all():
            if subscription.user_id == user_id and subscription.is_active():
                return True
                
        return False
    
    # 添加获取visibility可见性的接口
    @classmethod
    def get_visibility_options(cls):
        """获取所有可用的可见性选项
        
        Returns:
            list: 可见性选项列表
        """
        return ['public', 'private', 'organization']
    
    def get_visibility(self):
        """获取当前Agent的可见性
        
        Returns:
            str: 可见性值
        """
        return self.visibility
    
    def is_public(self):
        """判断Agent是否公开可见
        
        Returns:
            bool: 是否公开可见
        """
        return self.visibility == 'public'
    
    def is_private(self):
        """判断Agent是否私有
        
        Returns:
            bool: 是否私有
        """
        return self.visibility == 'private'
    
    def is_organization(self):
        """判断Agent是否组织可见
        
        Returns:
            bool: 是否组织可见
        """
        return self.visibility == 'organization'
    
    # 添加获取status状态的接口
    @classmethod
    def get_status_options(cls):
        """获取所有可用的状态选项
        
        Returns:
            list: 状态选项列表
        """
        return ['draft', 'published', 'archived']
    
    def get_status(self):
        """获取当前Agent的状态
        
        Returns:
            str: 状态值
        """
        return self.status
    
    def is_draft(self):
        """判断Agent是否为草稿状态
        
        Returns:
            bool: 是否为草稿状态
        """
        return self.status == 'draft'
    
    def is_published(self):
        """判断Agent是否已发布
        
        Returns:
            bool: 是否已发布
        """
        return self.status == 'published'
    
    def is_archived(self):
        """判断Agent是否已归档
        
        Returns:
            bool: 是否已归档
        """
        return self.status == 'archived'
    
    @classmethod
    def init_default_agents(cls, session, user_id):
        """初始化默认Agent"""
        # 获取或创建默认模型配置
        from .agent_model_config import AgentModelConfig
        default_model = session.query(AgentModelConfig).filter_by(model_name="deepseek-chat").first()
        if not default_model:
            default_model = AgentModelConfig.init_default_models(session)
        
        # 创建默认Agent
        default_agent = cls(
            key_id=str(uuid.uuid4()),
            user_id=user_id,
            name="默认助手",
            description="这是一个默认的AI助手",
            pricing=0.0,
            visibility="public",
            status="published",
            type="assistant",
            is_deleted=False,
            model_config_id=default_model.id  # 设置关联的模型配置ID
        )
        
        # 添加Agent到会话
        session.add(default_agent)
        
        return default_agent
    
  