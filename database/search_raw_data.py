from sqlalchemy import Column, String, LargeBinary, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import time
from datetime import datetime
import zlib
import json

class SearchRawData(Base):
    """搜索引擎原始数据模型，存储搜索引擎返回的原始数据"""
    __tablename__ = "search_raw_data"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invocation_id = Column(String(36), ForeignKey('agent_invocations.id'), nullable=False)
    engine_type = Column(String(20), nullable=False, comment='搜索引擎类型')
    content_type = Column(String(20), default='text', comment='内容类型：text/image/mixed')
    request = Column(JSON, nullable=False, comment='请求参数')
    response = Column(LargeBinary, nullable=False, comment='压缩后的原始响应')
    structured_data = Column(JSON, nullable=True, comment='结构化结果')
    cache_info = Column(JSON, nullable=True, comment='缓存信息')
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), comment='创建时间戳(毫秒)')
    
    # 关系
    invocation = relationship("AgentInvocation", back_populates="search_data")
    
    def __repr__(self):
        return f"<SearchRawData(id='{self.id}', engine_type='{self.engine_type}')>"
    
    def set_response(self, response_data):
        """设置响应数据，自动压缩"""
        if isinstance(response_data, dict) or isinstance(response_data, list):
            response_str = json.dumps(response_data)
        else:
            response_str = str(response_data)
        
        # 压缩数据
        self.response = zlib.compress(response_str.encode('utf-8'))
    
    def get_response(self):
        """获取解压后的响应数据"""
        if not self.response:
            return None
        
        # 解压数据
        decompressed = zlib.decompress(self.response).decode('utf-8')
        
        # 尝试解析JSON
        try:
            return json.loads(decompressed)
        except:
            return decompressed