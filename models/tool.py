from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class ToolType(str, Enum):
    API = "api"
    FUNCTION = "function"
    RSS = "rss"

class ToolBase(BaseModel):
    name: str
    tool_type: ToolType
    endpoint: Optional[str] = None
    description: Optional[str] = None
    config_params: Optional[Dict[str, Any]] = None

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    tool_type: Optional[ToolType] = None
    endpoint: Optional[str] = None
    description: Optional[str] = None
    config_params: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

class ToolResponse(ToolBase):
    id: str
    is_enabled: bool
    created_at: int
    updated_at: int
    
    class Config:
        orm_mode = True