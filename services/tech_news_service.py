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
            
            # 将NewsItem对象转换为可序列化的字典
            serializable_news = []
            for news in all_news:
                news_dict = {
                    'title': news.title,
                    'link': news.link,
                    'guid': news.guid,
                    'description': news.description,
                    'published_date': news.published_date.isoformat() if news.published_date else None,
                    'source': news.source,
                    'image_url': news.image_url,
                    'author': news.author,
                    'categories': news.categories,
                    'keywords': news.keywords,
                    'publisher': news.publisher,
                    'subject': news.subject
                }
                serializable_news.append(news_dict)
            
            return {
                'query': query,
                'news_items': serializable_news,
                'total_count': len(serializable_news)
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
        # 只使用 news_items 字段
        news_items = data.get('news_items', [])
        error = data.get('error', '')
        is_chinese = lang.startswith('zh')
        
        # 使用提供的提示词或默认提示词
        prompt_template = prompt
       
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
            
            # 将NewsItem对象转换为可序列化的字典
            serializable_items = []
            for item in news_items:
                if hasattr(item, '__dict__'):
                    # 如果是NewsItem对象，转换为字典
                    item_dict = {}
                    for key, value in item.__dict__.items():
                        if key.startswith('_'):
                            continue  # 跳过私有属性
                        
                        # 处理日期类型
                        if isinstance(value, datetime):
                            item_dict[key] = value.isoformat()
                        else:
                            item_dict[key] = value
                    
                    serializable_items.append(item_dict)
                else:
                    # 如果已经是字典，直接添加
                    serializable_items.append(item)
            
            # 保存新闻数据和总结
            self.rss_entry_dao.save_entry(
                title="科技新闻总结",
                description="自动生成的科技新闻总结",
                link="",
                published_date=datetime.now(),
                source="agent",
                categories=["tech", "news", "summary"],
                invocation_id=invocation_id,
                raw_data=serializable_items,  # 使用可序列化的字典列表
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
            # 检查item是否为字典类型
            if isinstance(item, dict):
                # 如果是字典，直接使用键值访问
                title = item.get('title', '无标题')
                description = item.get('description', '无描述')
                categories = item.get('categories', [])
                source = item.get('source', '未知来源')
                published_date = item.get('published_date', '')
                link = item.get('link', '#')
                
                # 处理published_date
                if isinstance(published_date, str) and published_date:
                    try:
                        # 尝试将ISO格式的日期字符串转换为datetime对象
                        published_date = datetime.fromisoformat(published_date).strftime('%Y-%m-%d')
                    except:
                        published_date = '未知日期'
                else:
                    published_date = '未知日期'
                
                # 处理categories
                if isinstance(categories, list):
                    categories_str = ', '.join(categories)
                else:
                    categories_str = str(categories)
            else:
                # 如果是NewsItem对象，使用属性访问
                title = item.title
                description = item.description
                categories_str = ', '.join(item.categories)
                source = item.source
                published_date = item.published_date.strftime('%Y-%m-%d')
                link = item.link
            
            # 格式化新闻项
            news_text += news_item_format.format(
                index=i,
                title=title,
                description=description,
                categories=categories_str,
                source=source,
                published_date=published_date,
                link=link
            )
        return news_text
