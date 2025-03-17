from sqlalchemy import Column, String, Integer, Date, Enum, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime

class Subscription(Base):
    """用户订阅模型，管理用户对Agent的订阅关系"""
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    agent_id = Column(String(36), ForeignKey('agents.key_id'), nullable=False)
    
    # 订阅时间范围
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # 支付和状态信息
    payment_status = Column(Enum('pending', 'paid', 'failed', 'refunded', name='payment_status_enum'), 
                           default='pending')
    status = Column(Enum('active', 'expired', 'cancelled', name='subscription_status_enum'), 
                   default='active')
    
    # 价格和续订信息
    price = Column(Float, nullable=False, comment='订阅时价格快照')
    renewal_count = Column(Integer, default=0, comment='续订次数')
    
    # 时间戳和删除标记
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)
    
    # 关系
    user = relationship("UserModel", back_populates="subscriptions")
    agent = relationship("Agent", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id='{self.id}', user_id='{self.user_id}', agent_id='{self.agent_id}', status='{self.status}')>"
    
    @property
    def is_active(self):
        """检查订阅是否处于活跃状态"""
        today = datetime.now().date()
        return (not self.is_deleted and 
                self.status == 'active' and 
                self.payment_status == 'paid' and
                self.start_date <= today <= self.end_date)
    
    @classmethod
    def get_active_subscriptions(cls, session, user_id):
        """获取用户的所有活跃订阅"""
        today = datetime.now().date()
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.status == 'active',
            cls.payment_status == 'paid',
            cls.start_date <= today,
            cls.end_date >= today,
            cls.is_deleted == False
        ).all()