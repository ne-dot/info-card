from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgentListRequest(BaseModel):
    """获取Agent列表的请求参数模型"""
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(10, description="每页数量")
    user_id: str = Field(..., description="用户ID")

class AgentCreateRequest(BaseModel):
    """创建Agent的请求参数模型"""
    name: str = Field(..., description="Agent名称")
    name_en: Optional[str] = Field("", description="Agent英文名称")
    name_zh: Optional[str] = Field("", description="Agent中文名称")
    description: Optional[str] = Field("", description="Agent描述")
    pricing: Optional[float] = Field(0.0, description="价格")
    visibility: Optional[str] = Field("public", description="可见性")
    status: Optional[str] = Field("draft", description="状态")