from typing import List, Optional, Tuple, Dict, Any
from utils.logger import setup_logger
from models.news import NewsItem
from tools.news_tools import get_wired_news, get_bbc_news
from services.tool_protocol import ToolProtocol
from utils.i18n_utils import get_text
from dao.rss_entry_dao import RSSEntryDAO
from datetime import datetime
import json

logger = setup_logger('tech_news_service')

class TechNewsService(ToolProtocol):
    """科技新闻服务，实现工具协议"""
    
    def __init__(self, db=None):
        """初始化科技新闻服务"""
        logger.info("初始化科技新闻服务")
        self.rss_entry_dao = RSSEntryDAO(db) if db else None
    
    @property
    def tool_name(self) -> str:
        return "tech_news"
    
    @property
    def tool_description(self) -> str:
        return "获取最新科技新闻"
    
    async def get_tool_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """获取科技新闻数据
        
        Args:
            query: 搜索查询
            **kwargs: 其他参数，可以包含:
                - limit: 每个来源的新闻数量，默认为5
                
        Returns:
            Dict[str, Any]: 包含新闻结果的字典
        """
        try:
            limit = kwargs.get('limit', 5)
            logger.info(f"获取科技新闻，限制每个来源 {limit} 条")
            
            # 获取Wired新闻
            wired_news = await get_wired_news(limit=limit)
            logger.info(f"获取到 {len(wired_news)} 条Wired新闻")
            
            # 获取BBC新闻
            bbc_news = await get_bbc_news(limit=limit)
            logger.info(f"获取到 {len(bbc_news)} 条BBC新闻")
            
            # 合并结果
            all_news = wired_news + bbc_news
            
            return {
                'query': query,
                'news_items': all_news,
                'total_count': len(all_news)
            }
            
        except Exception as e:
            logger.error(f"获取科技新闻失败: {str(e)}")
            return {
                'query': query,
                'news_items': [],
                'error': str(e)
            }
    
    def organize_prompt(self, data: Dict[str, Any], lang: str = 'en', prompt: str = None) -> Tuple[str, str]:
        """根据新闻结果组织提示词
        
        Args:
            data: 新闻结果数据
            lang: 语言，默认为英文
            prompt: 自定义系统提示词，如果提供则使用此提示词
            
        Returns:
            Tuple[str, str]: 包含(system_prompt, human_message)的元组
        """
        query = data.get('query', '')
        news_items = data.get('news_items', [])
        error = data.get('error', '')
        is_chinese = lang.startswith('zh')
        
        if error:
            system_prompt = error
            human_message = "获取新闻失败，请稍后再试。" if is_chinese else "Failed to get news, please try again later."
            return system_prompt, human_message
        
        if not news_items:
            system_prompt = "未找到新闻" if is_chinese else "No news found"
            human_message = "未找到相关新闻，请稍后再试。" if is_chinese else "No relevant news found, please try again later."
            return system_prompt, human_message
        
        # 使用提供的提示词或默认提示词
        prompt_template = prompt
        if not prompt_template:
            prompt_template = "请总结以下科技新闻的要点，并分析其中的技术趋势。" if is_chinese else "Please summarize the key points of the following tech news and analyze the technology trends."
        
        # 构建新闻文本
        news_item_format = get_text("news.news_item_format", lang)
        news_text = self._build_news_text(news_items, news_item_format)
        
        # 组合完整提示词
        system_prompt = f"{prompt_template}\n\n{'新闻内容:' if is_chinese else 'News content:'}\n{news_text}"
        
        # 构建人类消息
        human_message = get_text("news.summary_prompt", lang)
        
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
        if not self.rss_entry_dao:
            logger.warning("未提供RSSEntryDAO，无法保存新闻数据")
            return False
            
        try:
            invocation_id = kwargs.get('invocation_id')
            if not invocation_id:
                logger.warning("未提供invocation_id，无法保存新闻数据")
                return False
                
            news_items = data.get('news_items', [])
            if not news_items:
                logger.warning("没有新闻数据可保存")
                return False
                
            # 将新闻数据转换为JSON格式
            news_items_json = self._format_news_items(news_items)
            
            # 收集feed_ids（如果有的话）
            feed_ids = []
            for item in news_items:
                if hasattr(item, 'feed_id') and item.feed_id and item.feed_id not in feed_ids:
                    feed_ids.append(item.feed_id)
            
            # 保存新闻数据和总结
            self.rss_entry_dao.save_entry(
                title="科技新闻总结",
                description="自动生成的科技新闻总结",
                link="",
                published_date=datetime.now(),
                source="agent",
                categories=["tech", "news", "summary"],
                feed_ids=feed_ids,
                invocation_id=invocation_id,
                raw_data=news_items_json,
                summary=result
            )
            logger.info("新闻数据和总结已存储")
            return True
            
        except Exception as e:
            logger.error(f"保存新闻数据失败: {str(e)}")
            return False
    
    def _build_news_text(self, news_items: List[NewsItem], news_item_format: str) -> str:
        """构建新闻文本"""
        news_text = ""
        for i, item in enumerate(news_items, 1):
            news_text += news_item_format.format(
                index=i,
                title=item.title,
                description=item.description,
                categories=', '.join(item.categories),
                source=item.source,
                published_date=item.published_date.strftime('%Y-%m-%d'),
                link=item.link
            )
        return news_text
    
    def _format_news_items(self, news_items: List[NewsItem]) -> str:
        """将新闻项转换为JSON格式"""
        items_dict = []
        for item in news_items:
            item_dict = {
                'title': item.title,
                'link': item.link,
                'guid': item.guid,
                'description': item.description,
                'published_date': item.published_date.isoformat() if item.published_date else None,
                'source': item.source,
                'image_url': item.image_url,
                'author': item.author,
                'categories': item.categories,
                'keywords': item.keywords,
                'publisher': item.publisher,
                'subject': item.subject
            }
            items_dict.append(item_dict)
        
        return json.dumps(items_dict, ensure_ascii=False)