from services.tool_protocol import ToolProtocol
from utils.logger import setup_logger
from tools.google_search import search_google_by_text, search_google_by_image
from typing import Dict, Any, List, Optional, Tuple
from dao.search_raw_dao import SearchRawDAO
# 添加SummaryDAO的导入
from dao.ai_summary_dao import AISummaryDAO
import json

logger = setup_logger('google_search_service')

class GoogleSearchService(ToolProtocol):
    """Google搜索服务，实现工具协议"""
    
    def __init__(self, db=None):
        """初始化Google搜索服务"""
        logger.info("初始化Google搜索服务")
        self.search_raw_dao = SearchRawDAO(db) if db else None
        self.summary_dao = AISummaryDAO(db)
    
    @property
    def tool_name(self) -> str:
        return "google_search"
    
    @property
    def tool_description(self) -> str:
        return "搜索Google获取相关信息"
    
    async def get_tool_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """获取Google搜索数据
        
        Args:
            query: 搜索查询
            **kwargs: 其他参数
                
        Returns:
            Dict[str, Any]: 包含搜索结果的字典
        """
        try:
            logger.info(f"执行Google搜索，查询: {query}")
            
            # 获取文本搜索结果（5条）- 移除limit参数
            text_results = await search_google_by_text(query)
            logger.info(f"获取到 {len(text_results)} 条文本搜索结果")
            
            # 获取图片搜索结果（5条）- 移除limit参数
            image_results = await search_google_by_image(query)
            logger.info(f"获取到 {len(image_results)} 条图片搜索结果")
            
            # 合并结果
            return {
                'query': query,
                'text_results': text_results,
                'image_results': image_results
            }
            
        except Exception as e:
            logger.error(f"Google搜索失败: {str(e)}")
            return {
                'query': query,
                'text_results': [],
                'image_results': [],
                'error': str(e)
            }
    
    def organize_prompt(self, data: Dict[str, Any], lang: str = 'en', prompt: str = None) -> Tuple[str, str]:
        """根据搜索结果组织提示词
        
        Args:
            data: 搜索结果数据
            lang: 语言，默认为英文
            prompt: 自定义系统提示词，如果提供则使用此提示词
            
        Returns:
            Tuple[str, str]: 包含(system_prompt, human_message)的元组
        """
        query = data.get('query', '')
        text_results = data.get('text_results', [])
        image_results = data.get('image_results', [])
        error = data.get('error', '')
        
        # 构建搜索结果摘要
        search_summary = self._build_search_summary(text_results, image_results, error, lang)
        
        # 构建系统提示词，优先使用传入的prompt
        system_prompt = prompt if prompt else self._get_system_prompt(lang)
        
        # 构建人类消息
        human_message = self._build_human_message(query, search_summary, lang)
        
        return system_prompt, human_message
    
    async def save_tool_data(self, data: Dict[str, Any], result: str, **kwargs) -> bool:
        """保存工具数据和处理结果
        
        Args:
            data: 工具数据，通常是get_tool_data的返回值
            result: 处理结果，通常是AI生成的回复
            **kwargs: 其他参数，可能包含user_id, invocation_id等
            
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        if not self.search_raw_dao:
            logger.warning("未提供SearchRawDAO，无法保存搜索数据")
            return False
            
        try:
            invocation_id = kwargs.get('invocation_id')
            if not invocation_id:
                logger.warning("未提供invocation_id，无法保存搜索数据")
                return False
                
            query = data.get('query', '')
            text_results = data.get('text_results', [])
            image_results = data.get('image_results', [])
            lang = kwargs.get('lang', 'zh')
            
            # 保存文本搜索结果
            if text_results:
                # 构建更详细的结构化数据
                text_structured_data = {
                    "total_results": len(text_results),
                    "result_items": text_results  # 保存完整的结果项
                }
                
                self.search_raw_dao.create_search_data(
                    invocation_id=invocation_id,
                    engine_type="google",
                    content_type="text",
                    request_data={"query": query},
                    response_data=text_results,
                    structured_data=text_structured_data
                )
                logger.info(f"已保存 {len(text_results)} 条文本搜索结果")
            
            # 保存图片搜索结果
            if image_results:
                # 构建更详细的结构化数据
                image_structured_data = {
                    "total_results": len(image_results),
                    "result_items": image_results  # 保存完整的结果项
                }
                
                self.search_raw_dao.create_search_data(
                    invocation_id=invocation_id,
                    engine_type="google",
                    content_type="image",
                    request_data={"query": query},
                    response_data=image_results,
                    structured_data=image_structured_data
                )
                logger.info(f"已保存 {len(image_results)} 条图片搜索结果")
            
            # 保存AI生成的结果摘要
            if result and self.summary_dao:
                # 构建摘要元数据
                summary_metadata = {
                    'model': kwargs.get('model', 'unknown'),
                    'query': query,
                    'language': lang,
                    'text_sources_count': len(text_results),
                    'image_sources_count': len(image_results)
                }
                
                # 保存AI生成的摘要
                try:
                    self.summary_dao.create_summary(
                        invocation_id=invocation_id,
                        content=result,
                        metadata=summary_metadata
                    )
                    logger.info(f"已保存AI生成的摘要，长度: {len(result)}")
                except Exception as summary_error:
                    logger.error(f"保存AI摘要失败: {str(summary_error)}")
            elif result:
                logger.warning("未提供SummaryDAO，无法保存AI摘要")
            
            return True
            
        except Exception as e:
            logger.error(f"保存搜索数据失败: {str(e)}")
            return False
    
    def _build_search_summary(self, text_results, image_results, error, lang):
        """构建搜索结果摘要"""
        if lang.startswith('en'):
            summary = ""
            
            if error:
                summary += f"Error: {error}\n\n"
                return summary
            
            if not text_results and not image_results:
                summary += "No search results found.\n\n"
                return summary
            
            # 添加文本搜索结果
            if text_results:
                summary += "Web search results:\n\n"
                for i, result in enumerate(text_results, 1):
                    title = result.get('title', 'No title')
                    link = result.get('link', '#')
                    snippet = result.get('snippet', 'No description')
                    display_link = result.get('displayLink', 'Unknown source')
                    
                    summary += f"{i}. {title}\n"
                    summary += f"   URL: {link}\n"
                    summary += f"   Source: {display_link}\n"
                    summary += f"   {snippet}\n\n"
            
        else:
            summary = ""
            
            if error:
                summary += f"错误：{error}\n\n"
                return summary
            
            if not text_results and not image_results:
                summary += "未找到搜索结果。\n\n"
                return summary
            
            # 添加文本搜索结果
            if text_results:
                summary += "网页搜索结果：\n\n"
                for i, result in enumerate(text_results, 1):
                    title = result.get('title', '无标题')
                    link = result.get('link', '#')
                    snippet = result.get('snippet', '无描述')
                    display_link = result.get('displayLink', '未知来源')
                    
                    summary += f"{i}. {title}\n"
                    summary += f"   网址：{link}\n"
                    summary += f"   来源：{display_link}\n"
                    summary += f"   {snippet}\n\n"
        
        return summary
    
    def _build_human_message(self, query, search_summary, lang):
        """构建人类消息"""
        if lang.startswith('en'):
            return f"Question: \"{query}\"\n\nSearch results:\n{search_summary}\n\nPlease analyze these search results and provide a comprehensive summary according to the instructions."
        else:
            return f"问题：「{query}」\n\n搜索结果：\n{search_summary}\n\n请根据指示分析这些搜索结果并提供全面的总结。"
    
    def _get_system_prompt(self, lang):
        """获取系统提示词"""
        if lang.startswith('en'):
            return f"Question: \"{query}\"\n\nSearch results:\n{search_summary}\n\nPlease analyze these search results and provide a comprehensive summary according to the instructions."
        else:
            return f"问题：「{query}」\n\n搜索结果：\n{search_summary}\n\n请根据指示分析这些搜索结果并提供全面的总结。"
    