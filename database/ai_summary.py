from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import time
from datetime import datetime

class AISummary(Base):
    """AI总结结果模型，存储AI生成的总结内容"""
    __tablename__ = "ai_summaries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invocation_id = Column(String(36), ForeignKey('agent_invocations.id'), nullable=False, unique=True)
    content = Column(Text, nullable=False, comment='总结内容')
    meta_info = Column(JSON, nullable=False, comment='元数据')  # Changed from 'metadata' to 'meta_info'
    version_chain = Column(JSON, nullable=True, comment='版本链结构')
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), comment='创建时间戳(毫秒)')
    
    # 关系
    invocation = relationship("AgentInvocation", back_populates="summary")
    
    def __repr__(self):
        return f"<AISummary(id='{self.id}', invocation_id='{self.invocation_id}')>"
    
    @property
    def model(self):
        """获取使用的模型"""
        if self.meta_info and 'model' in self.meta_info:
            return self.meta_info['model']
        return None
    
    @property
    def quality_score(self):
        """获取质量评分"""
        if self.meta_info and 'quality_score' in self.meta_info:
            return self.meta_info['quality_score']
        return None