import feedparser
import time
from datetime import datetime
from utils.logger import setup_logger
import aiohttp
from models.news import NewsItem
from typing import List, Optional, Tuple, Dict, Any
from config.settings import NEWS_SETTINGS

logger = setup_logger('news_tools')

class NewsServiceTool:
    """新闻服务工具基类"""
    
    def __init__(self, feed_name=None, feed_category="tech", rss_url=None):
        self.feed_name = feed_name
        self.feed_category = feed_category
        self.rss_url = rss_url
        
    async def get_news(self, limit: int = 10) -> List[NewsItem]:
        """
        获取新闻
        
        Args:
            limit: 返回的新闻条数，默认10条
            
        Returns:
            List[NewsItem]: 新闻列表
        """
        try:
            if not self.rss_url:
                logger.error(f"{self.feed_name} RSS URL未设置")
                return []
                
            logger.info(f"开始获取{self.feed_name}新闻")
            
            # 使用aiohttp异步获取RSS内容
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    if response.status != 200:
                        logger.error(f"获取{self.feed_name} RSS失败: HTTP状态码 {response.status}")
                        return []
                    
                    content = await response.text()
            
            # 解析RSS内容
            feed = feedparser.parse(content)
            
            if not feed or not feed.entries:
                logger.warning(f"没有找到{self.feed_name}新闻条目")
                return []
            
            # 转换为NewsItem对象
            news_items = []
            for entry in feed.entries[:limit]:
                news_item = self._parse_entry(entry)
                if news_item:
                    news_items.append(news_item)
            
            logger.info(f"成功获取 {len(news_items)} 条{self.feed_name}新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"获取{self.feed_name}新闻失败: {str(e)}")
            return []
    
    def _parse_entry(self, entry):
        """解析RSS条目为NewsItem对象，子类可以重写此方法"""
        try:
            # 处理发布时间
            published = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            
            # 获取图片URL
            image_url = None
            if 'media_thumbnail' in entry and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0]['url']
            
            # 获取分类
            categories = []
            if hasattr(entry, 'category'):
                categories = [entry.category]
            elif hasattr(entry, 'categories'):
                categories = [cat for cat in entry.categories]
            
            # 获取关键词
            keywords = []
            if hasattr(entry, 'media_keywords'):
                keywords = entry.media_keywords.split(',')
            
            # 创建新闻项
            return NewsItem(
                title=entry.title,
                link=entry.link,
                guid=entry.guid if hasattr(entry, 'guid') else None,
                description=entry.description if hasattr(entry, 'description') else "",
                published_date=published,
                source=self.feed_name,
                image_url=image_url,
                author=entry.get('dc_creator', self.feed_name),
                categories=categories,
                keywords=keywords,
                publisher=entry.get('dc_publisher', None),
                subject=entry.get('dc_subject', None),
                feed_id=None  # 不使用feed_id
            )
        except Exception as e:
            logger.error(f"解析{self.feed_name}新闻条目失败: {str(e)}")
            return None


class WiredNewsServiceTool(NewsServiceTool):
    """Wired科技新闻服务工具"""
    
    def __init__(self):
        super().__init__(
            feed_name="Wired", 
            feed_category="tech",
            rss_url=NEWS_SETTINGS["rss_urls"].get("wired", "https://www.wired.com/feed/rss")
        )


class BBCNewsServiceTool(NewsServiceTool):
    """BBC新闻服务工具"""
    
    def __init__(self):
        super().__init__(
            feed_name="BBC", 
            feed_category="news",
            rss_url=NEWS_SETTINGS["rss_urls"].get("bbc", "http://feeds.bbci.co.uk/news/rss.xml")
        )
    
    def _parse_entry(self, entry):
        """重写解析方法以适应BBC RSS格式"""
        try:
            # 处理发布时间
            published = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            
            # 获取图片URL - BBC可能有不同的图片格式
            image_url = None
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if media.get('medium') == 'image':
                        image_url = media.get('url')
                        break
            
            # 获取描述 - BBC可能使用summary而不是description
            description = ""
            if hasattr(entry, 'description'):
                description = entry.description
            elif hasattr(entry, 'summary'):
                description = entry.summary
            
            # 创建新闻项
            return NewsItem(
                title=entry.title,
                link=entry.link,
                guid=entry.guid if hasattr(entry, 'guid') else None,
                description=description,
                published_date=published,
                source="BBC",
                image_url=image_url,
                author=entry.get('author', "BBC"),
                categories=entry.get('tags', []),
                keywords=[],
                publisher="BBC",
                subject=None,
                feed_id=None  # 不使用feed_id
            )
        except Exception as e:
            logger.error(f"解析BBC新闻条目失败: {str(e)}")
            return None


# 使用示例
async def get_wired_news(limit=10):
    """获取Wired新闻的工具函数"""
    service = WiredNewsServiceTool()
    return await service.get_news(limit)

async def get_bbc_news(limit=10):
    """获取BBC新闻的工具函数"""
    service = BBCNewsServiceTool()
    return await service.get_news(limit)