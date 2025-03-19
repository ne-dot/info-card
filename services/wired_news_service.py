import feedparser
import time
from datetime import datetime
from utils.logger import setup_logger
import aiohttp
from models.news import NewsItem
from typing import List, Optional, Tuple
from config.settings import NEWS_SETTINGS
from database.rss_feed import RSSFeed
from dao.rss_feed_dao import RSSFeedDAO  # 添加RSSFeedDAO导入

logger = setup_logger('news_service')

class WireNewsService:
    """Wired科技新闻服务"""
    
    def __init__(self, db=None):
        self.rss_url = NEWS_SETTINGS["rss_urls"]["wired"]
        self.rss_feed_dao = RSSFeedDAO(db) if db else None
        
    async def get_wired_news(self, limit: int = 10) -> Tuple[List[NewsItem], Optional[str]]:
        """
        获取Wired科技新闻
        
        Args:
            limit: 返回的新闻条数，默认10条
            
        Returns:
            Tuple[List[NewsItem], Optional[str]]: 新闻列表和feed_id
        """
        try:
            logger.info("开始获取Wired科技新闻")
            
            # 1. 使用RSSFeedDAO获取feed数据
            feed_id = None
            if self.rss_feed_dao:
                logger.info("尝试从数据库获取Wired feed")
               # 尝试获取特定的Wired feed
                feed = self.rss_feed_dao.get_feed_by_category_and_name("tech", "Wired")
                if feed:
                    logger.info(f"从数据库获取到Wired feed: id={feed.id}, name={feed.name}, url={feed.url}")
                    feed_id = feed.id
                    # 如果feed中有自定义URL，使用它
                    if feed.url:
                        self.rss_url = feed.url
            
            # 使用aiohttp异步获取RSS内容
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    if response.status != 200:
                        logger.error(f"获取Wired RSS失败: HTTP状态码 {response.status}")
                        return [], feed_id
                    
                    content = await response.text()
            
            # 解析RSS内容
            feed = feedparser.parse(content)
            
            if not feed or not feed.entries:
                logger.warning("没有找到Wired新闻条目")
                return [], feed_id
            
            # 转换为NewsItem对象
            news_items = []
            for entry in feed.entries[:limit]:
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
                news_item = NewsItem(
                    title=entry.title,
                    link=entry.link,
                    guid=entry.guid if hasattr(entry, 'guid') else None,
                    description=entry.description if hasattr(entry, 'description') else "",
                    published_date=published,
                    source="Wired",
                    image_url=image_url,
                    author=entry.get('dc_creator', "Wired"),
                    categories=categories,
                    keywords=keywords,
                    publisher=entry.get('dc_publisher', None),
                    subject=entry.get('dc_subject', None),
                    feed_id=feed_id  # 添加feed_id属性
                )
                news_items.append(news_item)
            
            logger.info(f"成功获取 {len(news_items)} 条Wired科技新闻")
            return news_items, feed_id
            
        except Exception as e:
            logger.error(f"获取Wired科技新闻失败: {str(e)}")
            return [], None
