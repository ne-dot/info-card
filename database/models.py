from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Table, Enum, DateTime, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import time
import uuid
from datetime import datetime

Base = declarative_base()

# 用户表定义
class UserModel(Base):
    __tablename__ = 'users'
    
    # 主键使用UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='用户唯一标识')
    
    # 身份验证系统 - 添加name参数
    auth_type = Column(Enum('email', 'anonymous', 'mobile', 'google', 'apple', name='auth_type_enum'), 
                       nullable=False, default='anonymous', comment='认证类型')
    auth_id = Column(String(255), comment='第三方ID/手机号/匿名UUID')
    
    # 认证补充字段 - SQLAlchemy不支持生成列，需要在应用层处理
    mobile = Column(String(20), unique=True, nullable=True, comment='手机号（仅mobile类型有效）')
    email = Column(String(100), unique=True, nullable=True, comment='邮箱（仅email类型有效）')
    
    # 安全信息
    password_hash = Column(String(255), nullable=True, comment='密码哈希（可选）')
    is_mobile_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    
    # 基础信息
    username = Column(String(50), comment='可编辑昵称')
    avatar_url = Column(String(255), nullable=True)
    
    # 时间信息
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间戳')
    updated_at = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment='更新时间戳')
    last_login_at = Column(Integer, nullable=True, comment='最后登录时间戳')
    
    # 状态管理 - 添加name参数
    account_status = Column(Enum('active', 'locked', 'deleted', name='account_status_enum'), default='active')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    
    # 关系
    external_auths = relationship("UserExternalAuth", back_populates="user", cascade="all, delete-orphan")
    
    # 索引在SQLAlchemy中通常在表创建时定义，这里只是注释说明
    # __table_args__ = (
    #     UniqueConstraint('auth_type', 'auth_id', name='uniq_auth'),
    #     Index('idx_mobile', 'mobile'),
    #     Index('idx_global_id', 'auth_id'),
    # )

# 第三方登录详情表
class UserExternalAuth(Base):
    __tablename__ = 'user_external_auths'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='主键')
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # 添加name参数
    provider = Column(Enum('google', 'apple', name='provider_enum'), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=True)
    expires_at = Column(Integer, nullable=True, comment='令牌过期时间戳')
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间戳')
    updated_at = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment='更新时间戳')
    
    # 关系
    user = relationship("UserModel", back_populates="external_auths")
    
    # 索引
    # __table_args__ = (
    #     UniqueConstraint('provider', 'provider_user_id', name='uniq_provider_user'),
    # )

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

# 新增 Agent 模型
class Agent(Base):
    """Agent 模型，用于存储智能代理配置"""
    __tablename__ = "agents"
    
    # 使用key_id作为主键，不再使用自增id
    key_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    name = Column(String(100), nullable=False)  # 默认名称
    name_en = Column(String(100), nullable=True)  # 英文名称
    name_zh = Column(String(100), nullable=True)  # 中文名称
    description = Column(Text, nullable=True)  # Agent的详细描述
    type = Column(String(50), nullable=False, default="assistant")  # agent类型，如 'assistant', 'search', 'expert' 等
    prompt_en = Column(Text, nullable=False)  # 英文提示词
    prompt_zh = Column(Text, nullable=True)  # 中文提示词
    model = Column(String(100), nullable=False)  # 使用的模型，如 'gpt-4', 'deepseek' 等
    tools = Column(Text, nullable=True)  # 存储工具配置，可以是JSON格式
    create_date = Column(Integer, default=lambda: int(time.time()))
    update_date = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))
    trigger_date = Column(Integer, nullable=True)  # 最后一次触发时间

