from sqlalchemy import Column, String, Text, Boolean, Integer, Enum, JSON, ForeignKey, Table
import time
import uuid
from .base import Base
from sqlalchemy.orm import relationship

# 定义中间表，用于 Agent 和 Tool 的多对多关系
agent_tool_mapping = Table(
    "agent_tool_mapping",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("agent_id", String(36), ForeignKey("agents.key_id"), nullable=False),
    Column("tool_id", String(36), ForeignKey("tools.id"), nullable=False)
)

class Tool(Base):
    """工具模型，用于存储各种工具的配置信息"""
    __tablename__ = 'tools'
    
    # 主键使用UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment='工具唯一标识')
    
    # 基本信息
    name = Column(String(100), nullable=False, comment='工具名称')
    description = Column(Text, nullable=True, comment='工具描述')
    
    # 工具类型
    tool_type = Column(Enum('api', 'function', 'rss', name='tool_type_enum'), 
                       nullable=False, comment='工具类型')
    
    # 端点信息
    endpoint = Column(String(255), nullable=True, comment='API端点或函数名称')
    
    # 状态
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    
    # 配置参数 (JSON类型)
    config_params = Column(JSON, nullable=True, comment='配置参数，JSON格式')
    
    # 时间信息
    created_at = Column(Integer, default=lambda: int(time.time()), comment='创建时间戳')
    updated_at = Column(Integer, default=lambda: int(time.time()), 
                        onupdate=lambda: int(time.time()), comment='更新时间戳')
    
    # 与 Agent 的多对多关系
    agents = relationship("Agent", secondary=agent_tool_mapping, back_populates="tools")