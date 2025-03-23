from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, DateTime, Table
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .base import Base

class RSSEntry(Base):
    """RSS内容条目模型，用于存储RSS源中的具体内容项"""
    __tablename__ = "rss_entries"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # 移除原来的feed_id字段，改为多对多关系
    invocation_id = Column(String(36), ForeignKey('agent_invocations.id'), nullable=False)
    
    # 基本信息
    guid = Column(String(512), nullable=False, comment='条目唯一标识')
    title = Column(String(1024), nullable=False)
    content = Column(Text, nullable=True, comment='完整内容（清洗后HTML）')
    summary = Column(Text, nullable=True, comment='AI生成摘要')
    
    # JSON数据
    raw_data = Column(JSON, nullable=True, comment='原始元数据')
    links = Column(JSON, nullable=True, comment='相关链接')
    
    # 时间信息
    published_at = Column(DateTime(6), nullable=False, comment='条目发布时间')
    processed_at = Column(DateTime(6), nullable=True, comment='被Agent处理时间')
    created_at = Column(DateTime(6), default=datetime.now, comment='创建时间')
    
    def __init__(self, guid, title, published_at, invocation_id, content=None, links=None, raw_data=None):
        self.id = str(uuid.uuid4())
        self.invocation_id = invocation_id
        self.guid = guid
        self.title = title
        self.content = content
        self.published_at = published_at
        self.links = links or {}
        self.raw_data = raw_data or {}
    
    def set_summary(self, summary, processed_at=None):
        """设置AI生成的摘要
        
        Args:
            summary: 摘要内容
            processed_at: 处理时间，默认为当前时间
        """
        self.summary = summary
        self.processed_at = processed_at or datetime.now()
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            "id": self.id,
            "guid": self.guid,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "links": self.links,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }