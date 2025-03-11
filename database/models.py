from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import time
import uuid

Base = declarative_base()

# 用户表定义
class UserModel(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)  # 允许为空，匿名用户没有邮箱
    password_hash = Column(String(100), nullable=False)
    created_at = Column(Integer, default=lambda: int(time.time()))  # 使用时间戳
    last_login = Column(Integer, nullable=True)  # 使用时间戳
    is_active = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)  # 添加匿名用户标记
    anonymous_id = Column(String(36), nullable=True)  # 匿名用户ID，用于关联转换前后的用户

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
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=True)  # 非匿名用户ID
    anonymous_id = Column(String(36), nullable=True)  # 匿名用户ID

# 搜索查询表定义
class SearchQueryModel(Base):
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)  # 修改为Text类型，避免长度限制
    date = Column(Integer, default=lambda: int(time.time()))  # 使用时间戳
    
    # 修改用户关联字段
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=True)  # 非匿名用户ID
    anonymous_id = Column(String(36), nullable=True)  # 匿名用户ID