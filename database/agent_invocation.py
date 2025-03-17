from sqlalchemy import Column, String, Text, Enum, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime
import time

class AgentInvocation(Base):
    """Agent调用记录模型，记录Agent的调用日志"""
    __tablename__ = "agent_invocations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, comment='触发用户')
    agent_id = Column(String(36), ForeignKey('agents.key_id'), nullable=False, comment='调用的Agent')
    # session_id在MySQL中是计算列，在SQLAlchemy中需要手动处理
    session_id = Column(String(36), nullable=True, comment='会话ID')
    input_text = Column(Text, nullable=False, comment='输入文本')
    input_params = Column(JSON, nullable=True, comment='扩展参数')
    status = Column(Enum('pending', 'processing', 'success', 'failed', name='invocation_status_enum'), 
                   default='pending', comment='处理状态')
    timestamps = Column(JSON, nullable=False, comment='时间戳记录')
    metrics = Column(JSON, nullable=True, comment='性能指标')
    error_logs = Column(JSON, nullable=True, comment='错误日志')
    # 将DateTime类型改为BigInteger类型，存储毫秒级时间戳
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000), comment='创建时间戳(毫秒)')
    
    # 关系
    user = relationship("UserModel", back_populates="invocations")
    agent = relationship("Agent", back_populates="invocations")
    summary = relationship("AISummary", back_populates="invocation", uselist=False, cascade="all, delete-orphan")
    search_data = relationship("SearchRawData", back_populates="invocation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentInvocation(id='{self.id}', agent_id='{self.agent_id}', status='{self.status}')>"
    
    def before_insert(self):
        """在插入前设置session_id"""
        if self.input_params and 'session_id' in self.input_params:
            self.session_id = self.input_params['session_id']
        else:
            self.session_id = self.id
    
    def set_start_time(self):
        """设置开始时间"""
        if not self.timestamps:
            self.timestamps = {}
        # 存储毫秒级时间戳
        self.timestamps['start'] = int(time.time() * 1000)
        self.status = 'processing'
    
    def set_end_time(self, success=True, error=None):
        """设置结束时间和状态"""
        if not self.timestamps:
            self.timestamps = {}
        # 存储毫秒级时间戳
        self.timestamps['end'] = int(time.time() * 1000)
        
        # 计算耗时
        if 'start' in self.timestamps:
            # 直接计算毫秒差值
            cost_time = self.timestamps['end'] - self.timestamps['start']
            
            if not self.metrics:
                self.metrics = {}
            self.metrics['cost_time'] = cost_time
        
        # 设置状态
        self.status = 'success' if success else 'failed'
        
        # 记录错误
        if error:
            if not self.error_logs:
                self.error_logs = {}
            self.error_logs['message'] = str(error)