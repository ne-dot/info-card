from sqlalchemy import Column, String, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import time

class SearchRawData(Base):
    """搜索原始数据模型，记录搜索引擎返回的原始数据"""
    __tablename__ = "search_raw_data"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invocation_id = Column(String(36), ForeignKey('agent_invocations.id'), nullable=False, comment='关联的调用ID')
    engine_type = Column(String(50), nullable=False, comment='搜索引擎类型')
    content_type = Column(String(50), nullable=False, comment='内容类型')
    request = Column(JSON, nullable=True, comment='请求数据')
    response = Column(JSON, nullable=True, comment='响应数据')
    structured_data = Column(JSON, nullable=True, comment='结构化数据')
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), comment='创建时间戳(毫秒)')
    
    # 关系
    invocation = relationship("AgentInvocation", back_populates="search_data")
    
    def __repr__(self):
        return f"<SearchRawData(id='{self.id}', engine_type='{self.engine_type}', content_type='{self.content_type}')>"