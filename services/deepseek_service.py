from langchain.chat_models.base import BaseChatModel
from langchain.schema import ChatResult, BaseMessage, ChatGeneration, AIMessage, HumanMessage, SystemMessage
from typing import List, Optional
from openai import OpenAI
from pydantic import Field
from utils.logger import setup_logger
from config.settings import DEEPSEEK_API_KEY

logger = setup_logger('deepseek_service')

class DeepSeekService(BaseChatModel):
    api_key: str = Field(..., description="DeepSeek API Key")
    client: Optional[OpenAI] = None
    model_name: str = Field(default="deepseek-chat")
    
    def __init__(self):
        super().__init__(api_key=DEEPSEEK_API_KEY)
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
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
        try:
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
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {str(e)}")
            raise

    @property
    def _llm_type(self) -> str:
        return "deepseek-chat"