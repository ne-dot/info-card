from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

class ModelConfigBase(BaseModel):
    """模型配置基础模型"""
    model_name: str = Field(..., description="模型名称，如gpt-4-turbo")
    weight: float = Field(1.0, description="流量分配权重")
    priority: int = Field(1, description="降级优先级")
    is_enabled: bool = Field(True, description="是否启用")
    config: Optional[Dict[str, Any]] = Field(None, description="模型特有参数")
    base_api_url: Optional[str] = Field(None, description="模型API基础URL")
    api_key: Optional[str] = Field(None, description="模型API密钥")
    
    class Config:
        # Replace orm_mode = True with from_attributes = True
        from_attributes = True

class ModelConfigCreate(ModelConfigBase):
    """创建模型配置请求模型"""

class ModelConfigUpdate(BaseModel):
    """更新模型配置请求模型"""
    model_name: Optional[str] = Field(None, description="模型名称")
    weight: Optional[float] = Field(None, description="流量分配权重")
    priority: Optional[int] = Field(None, description="降级优先级")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    config: Optional[Dict[str, Any]] = Field(None, description="模型特有参数")
    base_api_url: Optional[str] = Field(None, description="模型API基础URL")
    api_key: Optional[str] = Field(None, description="模型API密钥")

class ModelConfigResponse(BaseModel):
    """模型配置响应模型"""
    code: int
    message: str
    data: Optional[Dict[str, Any]]