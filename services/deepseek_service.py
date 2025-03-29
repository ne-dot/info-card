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
                full_response = {"role": "assistant", "content": "", "tool_calls": []}
                tool_call_chunks = {}  # 用于存储工具调用的分块
                
                for chunk in response:
                    delta = chunk.choices[0].delta
                    
                    # 打印接收到的数据块
                    logger.info(f"接收到数据块: {delta}")
                    
                    # 处理内容
                    if hasattr(delta, 'content') and delta.content is not None:
                        full_response["content"] += delta.content
                        logger.info(f"当前累积内容: {full_response['content']}")
                    
                    # 处理工具调用
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            tool_index = tool_call.index
                            
                            # 初始化工具调用
                            if tool_index not in tool_call_chunks:
                                tool_call_chunks[tool_index] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            
                            # 更新ID
                            if hasattr(tool_call, 'id') and tool_call.id:
                                tool_call_chunks[tool_index]["id"] = tool_call.id
                            
                            # 更新函数名
                            if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                tool_call_chunks[tool_index]["function"]["name"] = tool_call.function.name
                            
                            # 更新参数
                            if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                tool_call_chunks[tool_index]["function"]["arguments"] += tool_call.function.arguments
                
                # 合并工具调用
                for tool_chunk in tool_call_chunks.values():
                    full_response["tool_calls"].append(tool_chunk)
                
                logger.info(f"流式响应完成，最终结果: {full_response}")
                return full_response
            else:
                # 非流式响应处理
                logger.info(f"DeepSeek响应: {response}")
                return response.choices[0].message
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise e