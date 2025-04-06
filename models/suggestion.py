from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SuggestionGenerateRequest(BaseModel):
    """生成建议的请求参数模型"""
    query: Optional[str] = Field("", description="用户查询")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    chat_history: Optional[List[Dict[str, Any]]] = Field([], description="聊天历史")

    class Config:
        from_attributes = True 