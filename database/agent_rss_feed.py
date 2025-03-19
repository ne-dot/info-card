from sqlalchemy import Column, String, Integer, ForeignKey, JSON, DateTime, SmallInteger
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base

class AgentRSSFeed(Base):
    """Agent与RSS源关联模型，用于建立多对多关系"""
    __tablename__ = "agent_rss_feeds"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # 外键关联
    agent_id = Column(String(36), ForeignKey('agents.key_id'), nullable=False)
    feed_id = Column(String(36), ForeignKey('rss_feeds.id'), nullable=False)
    
    # 配置信息
    custom_filter = Column(JSON, nullable=True, comment='Agent专属过滤规则')
    priority = Column(SmallInteger, default=1)
    
    # 时间信息
    created_at = Column(DateTime(6), default=datetime.now)
    
    # 关系
    agent = relationship("Agent", back_populates="agent_feeds")
    feed = relationship("RSSFeed", back_populates="feed")
    
    def __init__(self, agent_id, feed_id, priority=1, custom_filter=None):
        self.id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.feed_id = feed_id
        self.priority = priority
        self.custom_filter = custom_filter or {}
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "feed_id": self.feed_id,
            "custom_filter": self.custom_filter,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }