from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgentListRequest(BaseModel):
    """获取Agent列表的请求参数模型"""
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(10, description="每页数量")
    user_id: str = Field(..., description="用户ID")

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class AgentCreateRequest(BaseModel):
    """创建Agent的请求参数模型"""
    name: str = Field(..., description="Agent名称")
    name_en: Optional[str] = Field("", description="Agent英文名称")
    name_zh: Optional[str] = Field("", description="Agent中文名称")
    description: Optional[str] = Field("", description="Agent描述")
    pricing: Optional[float] = Field(0.0, description="价格")
    visibility: Optional[str] = Field("public", description="可见性")
    status: Optional[str] = Field("draft", description="状态")

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class AgentConfigRequest(BaseModel):
    """Agent配置请求模型"""
    prompt_zh: Optional[str] = Field(None, description="中文提示词")
    prompt_en: Optional[str] = Field(None, description="英文提示词")
    tool_ids: Optional[List[str]] = Field(None, description="工具ID列表")
    model_id: Optional[str] = Field(None, description="模型ID")
    model_params: Optional[Dict[str, Any]] = Field(None, description="模型参数，如temperature、max_tokens等")
    
    class Config:
        from_attributes = True  # 使用新的配置名称
