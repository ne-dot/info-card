from langchain.schema import HumanMessage, SystemMessage
from utils.logger import setup_logger
import os
from openai import OpenAI

logger = setup_logger('deepseek_service')

class DeepSeekService:
    def __init__(self):
        # 初始化 DeepSeek 客户端
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        )
        # 设置默认模型
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        logger.info(f"初始化 DeepSeekService，使用模型: {self.model}")

    def invoke(self, messages, tools=None):
        try:
            # 记录调用信息
            logger.info(f"调用DeepSeek API，消息数: {len(messages)}")
            if tools:
                logger.info(f"使用工具: {[tool.name for tool in tools]}")
                
            # 准备工具格式
            tools_format = None
            if tools:
                tools_format = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "搜索查询"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    } for tool in tools
                ]
            
            # 转换消息角色
            formatted_messages = []
            for msg in messages:
                role = msg.type
                # 将 human 角色转换为 user
                if role == "human":
                    role = "user"
                # 将 ai 角色转换为 assistant
                elif role == "ai":
                    role = "assistant"
                
                formatted_messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            logger.info(f"格式化后的消息: {formatted_messages}")
                
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=tools_format,
                tool_choice="auto" if tools else None,
                temperature=0.7,
                max_tokens=2000
            )
            
            logger.info(f"DeepSeek响应: {response}")
            
            # 返回结果
            return response.choices[0].message
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise e