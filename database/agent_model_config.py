from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base
import uuid
import json

class AgentModelConfig(Base):
    """Agent多模型配置表"""
    __tablename__ = "agent_model_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    model_name = Column(String(50), nullable=False, comment='如gpt-4-turbo')
    weight = Column(Float, default=1.0, comment='流量分配权重')
    priority = Column(Integer, default=1, comment='降级优先级')
    is_enabled = Column(Boolean, default=True)
    config = Column(Text, comment='模型特有参数，JSON格式')
    # 新增字段
    base_api_url = Column(String(255), nullable=True, comment='模型API基础URL')
    api_key = Column(String(255), nullable=True, comment='模型API密钥')
    
    # 关系
    agents = relationship("Agent", back_populates="model_config")
    
    @classmethod
    def init_default_models(cls, session):
        """初始化默认模型配置"""
        # 创建 deepseek 模型配置
        deepseek_config = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95
        }
        
        deepseek_model = cls(
            id=str(uuid.uuid4()),
            model_name="deepseek-chat",
            weight=0.7,
            priority=2,
            is_enabled=True,
            config=json.dumps(deepseek_config),
            base_api_url="https://api.deepseek.com/v1",  # 默认API URL
            api_key=None  # 默认为空，需要用户配置
        )
        
        # 添加到会话
        session.add(deepseek_model)
        session.flush()  # 确保模型有ID
        
        return deepseek_model