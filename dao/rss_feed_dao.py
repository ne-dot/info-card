from database.rss_feed import RSSFeed
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('rss_feed_dao')

class RSSFeedDao:
    """RSS订阅源数据访问对象"""
    
    def __init__(self, db):
        """初始化DAO
        
        Args:
            db: 数据库会话工厂
        """
        self.db = db
    
    def create_feed(self, feed_url, title, category='news', language='zh', etag=None, last_modified=None):
        """创建新的RSS订阅源
        
        Args:
            feed_url: RSS源URL
            title: 源标题
            category: 分类
            language: 语言代码
            etag: HTTP缓存标识
            last_modified: 最后修改时间
            
        Returns:
            RSSFeed: 创建的RSS订阅源对象，失败返回None
        """
        try:
            with self.db.get_session() as session:
                # 检查是否已存在相同URL的源
                existing = session.query(RSSFeed).filter(RSSFeed.feed_url == feed_url).first()
                if existing:
                    logger.info(f"RSS源已存在: {feed_url}")
                    return existing
                
                # 创建新源
                feed = RSSFeed(
                    feed_url=feed_url,
                    title=title,
                    category=category,
                    language=language,
                    etag=etag,
                    last_modified=last_modified
                )
                session.add(feed)
                session.commit()
                logger.info(f"创建RSS源成功: {title} ({feed_url})")
                return feed
        except SQLAlchemyError as e:
            logger.error(f"创建RSS源失败: {str(e)}")
            return None
    
    def get_feed_by_id(self, feed_id):
        """根据ID获取RSS源
        
        Args:
            feed_id: RSS源ID
            
        Returns:
            RSSFeed: RSS源对象，不存在返回None
        """
        try:
            with self.db.get_session() as session:
                return session.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
        except SQLAlchemyError as e:
            logger.error(f"获取RSS源失败: {str(e)}")
            return None
    
    def get_feed_by_url(self, feed_url):
        """根据URL获取RSS源
        
        Args:
            feed_url: RSS源URL
            
        Returns:
            RSSFeed: RSS源对象，不存在返回None
        """
        try:
            with self.db.get_session() as session:
                return session.query(RSSFeed).filter(RSSFeed.feed_url == feed_url).first()
        except SQLAlchemyError as e:
            logger.error(f"获取RSS源失败: {str(e)}")
            return None
    
    def get_all_feeds(self, category=None, language=None, limit=100, offset=0):
        """获取所有RSS源
        
        Args:
            category: 可选，按分类筛选
            language: 可选，按语言筛选
            limit: 返回数量限制
            offset: 分页偏移量
            
        Returns:
            list: RSS源对象列表
        """
        try:
            with self.db.get_session() as session:
                query = session.query(RSSFeed)
                
                if category:
                    query = query.filter(RSSFeed.category == category)
                
                if language:
                    query = query.filter(RSSFeed.language == language)
                
                # 按更新时间排序
                query = query.order_by(RSSFeed.updated_at.desc())
                
                return query.limit(limit).offset(offset).all()
        except SQLAlchemyError as e:
            logger.error(f"获取RSS源列表失败: {str(e)}")
            return []
    
    def update_feed(self, feed_id, **kwargs):
        """更新RSS源信息
        
        Args:
            feed_id: RSS源ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db.get_session() as session:
                feed = session.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
                if not feed:
                    logger.warning(f"更新失败，RSS源不存在: {feed_id}")
                    return False
                
                # 更新提供的字段
                for key, value in kwargs.items():
                    if hasattr(feed, key):
                        setattr(feed, key, value)
                
                session.commit()
                logger.info(f"更新RSS源成功: {feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新RSS源失败: {str(e)}")
            return False
    
    def update_feed_health(self, feed_id, success=True):
        """更新RSS源健康状态
        
        Args:
            feed_id: RSS源ID
            success: 是否成功获取RSS源
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db.get_session() as session:
                feed = session.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
                if not feed:
                    logger.warning(f"更新健康状态失败，RSS源不存在: {feed_id}")
                    return False
                
                feed.update_health_status(success)
                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新RSS源健康状态失败: {str(e)}")
            return False
    
    def delete_feed(self, feed_id):
        """删除RSS源
        
        Args:
            feed_id: RSS源ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            with self.db.get_session() as session:
                feed = session.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
                if not feed:
                    logger.warning(f"删除失败，RSS源不存在: {feed_id}")
                    return False
                
                session.delete(feed)
                session.commit()
                logger.info(f"删除RSS源成功: {feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"删除RSS源失败: {str(e)}")
            return False


class RSSFeedDAO:
    def __init__(self, db):
        self.db = db
    
    def get_feed_by_category_and_name(self, category: str, name: str) -> Optional[RSSFeed]:
        """根据分类和名称获取RSS Feed
        
        Args:
            category: Feed分类
            name: Feed名称
            
        Returns:
            Optional[RSSFeed]: 找到的Feed，如果不存在则返回None
        """
        session = self.db.get_session()
        try:
            feed = session.query(RSSFeed).filter(
                RSSFeed.category == category,
                RSSFeed.name == name
            ).first()
            return feed
        except Exception as e:
            logger.error(f"获取Feed失败: {str(e)}")
            return None
        finally:
            session.close()