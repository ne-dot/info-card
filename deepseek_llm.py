from langchain.chat_models.base import BaseChatModel
from langchain.schema import ChatResult, BaseMessage, ChatGeneration, AIMessage, HumanMessage, SystemMessage
from typing import List, Optional, Any, Dict
from openai import OpenAI
from pydantic import Field

class DeepSeekChat(BaseChatModel):
    api_key: str = Field(..., description="DeepSeek API Key")
    client: Optional[OpenAI] = None
    model_name: str = Field(default="deepseek-chat")
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def _convert_message_to_role(self, message: BaseMessage) -> str:
        if isinstance(message, SystemMessage):
            return "system"
        elif isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        else:
            raise ValueError(f"不支持的消息类型: {type(message)}")

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        converted_messages = [
            {
                "role": self._convert_message_to_role(m),
                "content": m.content
            } 
            for m in messages
        ]
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=converted_messages,
            stream=False
        )
        
        message = AIMessage(content=response.choices[0].message.content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _llm_type(self) -> str:
        return "deepseek-chat"