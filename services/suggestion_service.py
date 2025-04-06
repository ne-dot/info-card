from services.tool_protocol import ToolProtocol
from utils.logger import setup_logger
from typing import Dict, Any, List, Tuple
from dao.suggestion_dao import SuggestionDAO
import json
import re

logger = setup_logger('suggestion_service')

class SuggestionService(ToolProtocol):
    """推荐问题服务，实现工具协议"""
    
    def __init__(self, db=None):
        """初始化推荐问题服务"""
        logger.info("初始化推荐问题服务")
        self.suggestion_dao = SuggestionDAO(db) if db else None
    
    @property
    def tool_name(self) -> str:
        return "suggestion"
    
    @property
    def tool_description(self) -> str:
        return "生成并管理AI推荐问题"
    
    async def get_tool_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """获取推荐问题数据
        
        Args:
            query: 用户查询
            **kwargs: 其他参数，可能包含agent_id, user_id, chat_history等
                
        Returns:
            Dict[str, Any]: 包含查询的字典
        """
        try:
            logger.info(f"准备生成推荐问题，基于查询: {query}")
            
            # 直接返回查询和其他相关参数
            return {
                'query': query,
                'agent_id': kwargs.get('agent_id'),
                'user_id': kwargs.get('user_id'),
                'chat_history': kwargs.get('chat_history', [])
            }
            
        except Exception as e:
            logger.error(f"获取推荐问题数据失败: {str(e)}")
            return {
                'query': query,
                'error': str(e)
            }
    
    def organize_prompt(self, data: Dict[str, Any], lang: str = 'en', prompt: str = None) -> Tuple[str, str]:
        """根据数据组织提示词
        
        Args:
            data: 工具数据
            lang: 语言，默认为英文
            prompt: 自定义系统提示词，如果提供则使用此提示词
            
        Returns:
            Tuple[str, str]: 包含(system_prompt, human_message)的元组
        """
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        
        # 构建系统提示词，优先使用传入的prompt
        system_prompt = prompt
        
        # 构建人类消息，包含查询和聊天历史
        human_message = self._build_human_message(query, chat_history, lang)
        
        return system_prompt, human_message
    
    async def save_tool_data(self, data: Dict[str, Any], result: str, **kwargs) -> bool:
        """保存工具数据和处理结果
        
        Args:
            data: 工具数据，通常是get_tool_data的返回值
            result: 处理结果，通常是AI生成的推荐问题列表
            **kwargs: 其他参数，可能包含agent_id, user_id, invocation_id等
            
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        if not self.suggestion_dao:
            logger.warning("未提供SuggestionDAO，无法保存推荐问题")
            return False
            
        try:
            agent_id = data.get('agent_id') or kwargs.get('agent_id')
            user_id = data.get('user_id') or kwargs.get('user_id')
            query = data.get('query', '')
            lang = kwargs.get('lang', 'zh')
            
            # 解析AI生成的推荐问题列表
            suggestions = self._parse_suggestions(result)
            
            if not suggestions:
                logger.warning("未能解析出有效的推荐问题")
                return False
            
            # 保存每个推荐问题
            for suggestion_text in suggestions:
                await self.suggestion_dao.create_suggestion(
                    agent_id=agent_id,
                    content=suggestion_text,
                    user_id=user_id,
                    context=query,  # 使用原始查询作为上下文
                    language=lang
                )
            
            logger.info(f"已保存 {len(suggestions)} 条推荐问题")
            return True
            
        except Exception as e:
            logger.error(f"保存推荐问题失败: {str(e)}")
            # 打印更详细的错误信息
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False
    
    def _parse_suggestions(self, result: str) -> List[str]:
        """解析AI生成的推荐问题
        
        Args:
            result: AI生成的回复，JSON格式的推荐问题列表
            
        Returns:
            List[str]: 推荐问题列表
        """
        try:
            # 解析JSON字符串
            data = json.loads(result)
            
            # 如果JSON中包含suggestions字段
            if isinstance(data, dict) and 'suggestions' in data and isinstance(data['suggestions'], list):
                suggestions = []
                for item in data['suggestions']:
                    if isinstance(item, str) and 3 <= len(item) <= 200:
                        suggestions.append(item)
                
                return suggestions
            else:
                raise ValueError("JSON中未找到有效的suggestions字段")
                
        except Exception as e:
            logger.error(f"解析推荐问题失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # 直接抛出异常，不进行回退处理
    
    def _build_human_message(self, query: str, chat_history: List[Dict], lang: str) -> str:
        """构建人类消息
        
        Args:
            query: 用户查询
            chat_history: 聊天历史
            lang: 语言
            
        Returns:
            str: 人类消息
        """
        # 格式化聊天历史
        history_text = self._format_chat_history(chat_history, lang)
        
        # 处理query为空的情况
        if not query:
            if lang.startswith('en'):
                if history_text:
                    return f"Based on the following conversation:\n\n{history_text}\n\nPlease suggest 3-5 general questions that users might be interested in asking."
                else:
                    return "Please suggest 3-5 general questions that users might be interested in asking."
            else:
                if history_text:
                    return f"基于以下对话：\n\n{history_text}\n\n请推荐3-5个用户可能感兴趣的一般性问题。"
                else:
                    return "请推荐3-5个用户可能感兴趣的一般性问题。"
        
        # 处理正常情况
        if lang.startswith('en'):
            if history_text:
                return f"Based on the following conversation:\n\n{history_text}\n\nCurrent query: \"{query}\"\n\nPlease suggest 3-5 follow-up questions that the user might be interested in asking next."
            else:
                return f"Current query: \"{query}\"\n\nPlease suggest 3-5 follow-up questions that the user might be interested in asking next."
        else:
            if history_text:
                return f"基于以下对话：\n\n{history_text}\n\n当前问题：「{query}」\n\n请推荐3-5个用户可能感兴趣的后续问题。"
            else:
                return f"当前问题：「{query}」\n\n请推荐3-5个用户可能感兴趣的后续问题。"
    
    def _format_chat_history(self, chat_history: List[Dict], lang: str) -> str:
        """格式化聊天历史
        
        Args:
            chat_history: 聊天历史列表
            lang: 语言
            
        Returns:
            str: 格式化后的聊天历史文本
        """
        if not chat_history:
            return ""
        
        formatted_history = ""
        
        for i, message in enumerate(chat_history):
            role = message.get('role', '')
            content = message.get('content', '')
            
            if lang.startswith('en'):
                role_display = "User" if role == "user" else "Assistant"
            else:
                role_display = "用户" if role == "user" else "助手"
            
            formatted_history += f"{role_display}: {content}\n\n"
        
        return formatted_history
    