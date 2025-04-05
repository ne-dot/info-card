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

    def invoke(self, messages, tools=None, stream=False):
        try:
            # 记录调用信息
            logger.info(f"调用DeepSeek API，消息: {messages}")
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
                
            # 调用API，支持流式请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=tools_format,
                tool_choice="auto" if tools else None,
                temperature=0.7,
                max_tokens=2000,
                stream=stream  # 启用流式请求
            )
            
            # 处理流式响应
            if stream:
                logger.info("开始接收流式响应...")
                
                # 直接返回流式响应生成器
                async def response_generator():
                    full_content = ""
                    for chunk in response:
                        delta = chunk.choices[0].delta
                        
                        # 处理内容
                        if hasattr(delta, 'content') and delta.content is not None:
                            full_content += delta.content
                            # 实时返回内容块
                            yield {"content": delta.content, "full_content": full_content}
                        
                        # 处理工具调用
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                # 返回工具调用信息
                                yield {"tool_call": tool_call}
                
                # 返回异步生成器
                return response_generator()
            else:
                # 非流式响应处理
                logger.info(f"DeepSeek响应: {response}")
                return response.choices[0].message
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise e