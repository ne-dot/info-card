from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import time

class Subscription(Base):
    """订阅模型，用于存储用户对Agent的订阅信息"""
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, comment='用户ID')
    agent_id = Column(String(36), ForeignKey('agents.key_id'), nullable=False, comment='Agent ID')
    
    # 订阅信息
    start_date = Column(Integer, nullable=False, comment='订阅开始时间')
    end_date = Column(Integer, nullable=True, comment='订阅结束时间')
    price = Column(Float, default=0.0, comment='订阅价格')
    status = Column(String(20), default='active', comment='订阅状态')
    
    # 审计字段
    create_date = Column(Integer, default=lambda: int(time.time()), comment='创建时间')
    update_date = Column(Integer, default=lambda: int(time.time()), 
                         onupdate=lambda: int(time.time()), comment='更新时间')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    
    # 关系
    agent = relationship("Agent", back_populates="subscriptions")
    user = relationship("UserModel", back_populates="subscriptions")
    
    def is_active(self):
        """检查订阅是否有效"""
        current_time = int(time.time())
        return (self.status == 'active' and 
                self.start_date <= current_time and 
                (self.end_date is None or self.end_date >= current_time) and
                not self.is_deleted)