from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Table, Enum, DateTime, func, text, Float
from sqlalchemy.orm import relationship
import time
import uuid
from datetime import datetime

# Import Base from the base module instead of defining it here
from .base import Base

# 导入移动到单独文件的类
from .agent_model_config import AgentModelConfig
from .user_models import UserModel, UserExternalAuth
from .agent_prompt import AgentPrompt
from .agent import Agent

# 搜索结果表定义
class SearchResultModel(Base):
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    key_id = Column(String(36), unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    source = Column(String(50), nullable=True)
    type = Column(String(20), default='text')
    thumbnail_link = Column(String(500), nullable=True)
    context_link = Column(String(500), nullable=True)
    date = Column(Integer, default=lambda: int(time.time()))  # 使用时间戳
    
    # 外键关联到查询
    query_id = Column(Integer, ForeignKey('search_queries.id'))
    
    # 添加用户ID和匿名ID字段
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # 非匿名用户ID
    anonymous_id = Column(String(36), nullable=True)  # 匿名用户ID

# 搜索查询表定义
class SearchQueryModel(Base):
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)  # 修改为Text类型，避免长度限制
    date = Column(Integer, default=lambda: int(time.time()))  # 使用时间戳
    
    # 修改用户关联字段
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # 非匿名用户ID
    anonymous_id = Column(String(36), nullable=True)  # 匿名用户ID


# 首先定义映射表
news_trigger_mapping = Table(
    "news_trigger_mapping",
    Base.metadata,
    Column("id", Integer, primary_key=True),  # 添加自增主键
    Column("news_id", Integer, ForeignKey("news.id"), nullable=False),
    Column("trigger_id", String(36), ForeignKey("news_summary_triggers.key_id"), nullable=False)
)

# 然后定义 News 类
class News(Base):
    """新闻数据表模型"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    link = Column(String(512), nullable=False)
    published_date = Column(String(50), nullable=False)  
    source = Column(String(50), nullable=False)  # 'wired', 'bbc' 等
    categories = Column(String(255), nullable=True)  # 以逗号分隔的分类
    
    # 与触发记录的关系
    triggers = relationship("NewsSummaryTrigger", secondary=news_trigger_mapping, back_populates="news_items")

class NewsSummary(Base):
    """新闻AI总结数据表模型"""
    __tablename__ = "news_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_content = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="en")
    created_at = Column(Integer, default=lambda: int(time.time()))
    type = Column(String(50), default="auto")
    
    # 修改关系名称为 triggers
    triggers = relationship("NewsSummaryTrigger", back_populates="summary")

# 最后定义 NewsSummaryTrigger 类
class NewsSummaryTrigger(Base):
    """新闻总结触发记录表"""
    __tablename__ = "news_summary_triggers"
    
    key_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    summary_id = Column(Integer, ForeignKey("news_summaries.id"), nullable=True)
    agent_id = Column(String(36), ForeignKey("agents.key_id"), nullable=True)
    trigger_type = Column(String(50), nullable=False)  # 'manual', 'scheduled' 等
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # 如果是用户触发的，记录用户ID
    ip_address = Column(String(50), nullable=True)  # 记录请求IP
    success = Column(Boolean, default=True)  # 是否成功生成
    error_message = Column(Text, nullable=True)  # 如果失败，记录错误信息
    created_at = Column(Integer, default=lambda: int(time.time()))  # 使用时间戳
    
    # 与摘要的一对一关系
    summary = relationship("NewsSummary", back_populates="triggers")
    news_items = relationship("News", secondary=news_trigger_mapping, back_populates="triggers")
    agent = relationship("Agent")

# Agent类已移至单独文件

