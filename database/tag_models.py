from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
import time
import uuid
from .base import Base

class TagModel(Base):
    __tablename__ = 'tags'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='标签唯一标识')
    
    # 用户ID
    user_id = Column(String(36), nullable=False, comment='用户ID')
    
    # 标签名称
    name = Column(String(50), nullable=False, comment='标签名称')
    
    # 标签描述
    description = Column(String(255), nullable=True, comment='标签描述')
    
    # 时间信息
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间戳')
    updated_at = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment='更新时间戳')
    
    # 状态
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>" 