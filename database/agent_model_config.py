from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import json

class AgentModelConfig(Base):
    """Agent多模型配置表"""
    __tablename__ = "agent_model_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.key_id"), nullable=False)
    model_name = Column(String(50), nullable=False, comment='如gpt-4-turbo')
    weight = Column(Float, default=1.0, comment='流量分配权重')
    priority = Column(Integer, default=1, comment='降级优先级')
    is_enabled = Column(Boolean, default=True)
    config = Column(Text, comment='模型特有参数，JSON格式')
    
    # 关系
    agent = relationship("Agent", back_populates="model_configs")
    
    @classmethod
    def init_default_models(cls, session, agent_id):
        """初始化默认模型配置"""
        # 创建 deepseek 模型配置
        deepseek_config = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95
        }
        
        deepseek_model = cls(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            model_name="deepseek-chat",
            weight=0.7,
            priority=2,
            is_enabled=True,
            config=json.dumps(deepseek_config)
        )
        
        # 创建 gpt-4-turbo 模型配置
        # gpt4_config = {
        #     "temperature": 0.8,
        #     "max_tokens": 4000,
        #     "top_p": 1.0
        # }
        
        # gpt4_model = cls(
        #     id=str(uuid.uuid4()),
        #     agent_id=agent_id,
        #     model_name="gpt-4-turbo",
        #     weight=0.3,
        #     priority=1,
        #     is_enabled=True,
        #     config=json.dumps(gpt4_config)
        # )
        
        # 添加到会话
        session.add(deepseek_model)
        # session.add(gpt4_model)
        
        return [deepseek_model]