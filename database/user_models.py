from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import time
import uuid
from .models import Base

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