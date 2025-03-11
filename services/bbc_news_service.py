import feedparser
from datetime import datetime
import aiohttp
from typing import List, Optional
from models.news import NewsItem
from utils.logger import setup_logger

logger = setup_logger('bbc_news_service')

class BBCNewsService:
    """BBC科技新闻服务"""
    
    def __init__(self):
        self.rss_url = "https://feeds.bbci.co.uk/news/technology/rss.xml"
    
    async def get_bbc_news(self, limit: int = 10) -> List[NewsItem]:
        """
        获取BBC科技新闻
        
        Args:
            limit: 返回的新闻数量
            
        Returns:
            List[NewsItem]: 新闻项列表
        """
        try:
            logger.info(f"开始获取BBC科技新闻，数量: {limit}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    if response.status != 200:
                        logger.error(f"获取BBC新闻失败，状态码: {response.status}")
                        return []
                    
                    content = await response.text()
            
            # 解析RSS内容
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.warning("未找到BBC新闻条目")
                return []
            
            # 转换为NewsItem对象
            news_items = []
            for entry in feed.entries[:limit]:
                try:
                    # 解析日期 - BBC使用pubDate字段
                    published_date = datetime.strptime(
                        entry.pubDate, "%a, %d %b %Y %H:%M:%S %Z"
                    ) if hasattr(entry, 'pubDate') else datetime.now()
                    
                    # BBC科技新闻默认分类
                    categories = ["Technology"]
                    
                    # 获取缩略图URL
                    image_url = None
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0]['url']
                    
                    news_item = NewsItem(
                        title=entry.title,
                        description=entry.description,  # 使用description而不是summary
                        link=entry.link,
                        published_date=published_date,
                        categories=categories,
                        source="BBC Technology",
                        image_url=image_url if 'image_url' in NewsItem.__fields__ else None  # 如果模型支持image_url字段
                    )
                    news_items.append(news_item)
                except Exception as e:
                    logger.error(f"解析BBC新闻条目失败: {str(e)}")
                    continue
            
            logger.info(f"成功获取BBC科技新闻，共{len(news_items)}条")
            return news_items
            
        except Exception as e:
            logger.error(f"获取BBC科技新闻失败: {str(e)}")
            return []