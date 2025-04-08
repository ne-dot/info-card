from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, Integer, DateTime
from sqlalchemy.orm import relationship
import time
import uuid
from .base import Base

class FavoriteModel(Base):
    __tablename__ = 'favorites'
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='收藏记录唯一标识')
    
    # 用户ID
    user_id = Column(String(36), nullable=False, comment='用户ID')
    
    # 收藏类型
    source_type = Column(Enum('google', 'ai', name='source_type_enum'), 
                        nullable=False, comment='收藏来源类型：google搜索或AI搜索')
    
    # 收藏内容
    title = Column(String(255), nullable=True, comment='收藏内容标题')
    content = Column(Text, nullable=True, comment='收藏内容详情')
    url = Column(String(512), nullable=True, comment='收藏内容URL')
    image_url = Column(String(512), nullable=True, comment='收藏内容图片URL')
    
    # 标签ID
    tag_id = Column(String(36), ForeignKey('tags.id'), nullable=True, comment='关联的标签ID')
    
    # 时间信息
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间戳')
    updated_at = Column(Integer, default=lambda: int(time.time()), onupdate=lambda: int(time.time()), comment='更新时间戳')
    
    # 状态
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    
    # 关联关系
    tag = relationship("TagModel", backref="favorites")
    
    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, source_type={self.source_type}, title={self.title})>" 