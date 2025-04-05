from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
import time
import uuid
from .base import Base

class Suggestion(Base):
    """AI推荐问题表"""
    __tablename__ = "suggestions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.key_id"), nullable=True, comment='关联的Agent ID')
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True, comment='关联的用户ID')
    content = Column(Text, nullable=False, comment='推荐问题内容')
    context = Column(Text, nullable=True, comment='生成推荐的上下文')
    language = Column(String(10), default='zh', comment='问题语言(zh/en)')
    is_used = Column(Boolean, default=False, comment='是否被用户使用过')
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间')
    updated_at = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment='更新时间')
    
    # 关系
    agent = relationship("Agent", back_populates="suggestions")
    user = relationship("UserModel", back_populates="suggestions")