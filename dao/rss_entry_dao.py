from database.rss_entry import RSSEntry
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from utils.logger import setup_logger
from database.rss_feed import RSSFeed
import uuid
from datetime import datetime
from typing import List, Optional

logger = setup_logger('rss_entry_dao')

class RSSEntryDAO:
    def __init__(self, db):
        self.db = db
        self.session = db.get_session()
    
    def save_entry(self, title, description, link, published_date, source, categories, feed_ids, invocation_id=None, raw_data=None, summary=None):
        """保存RSS条目到数据库
        
        Args:
            title: 标题
            description: 描述
            link: 链接
            published_date: 发布日期
            source: 来源
            categories: 分类列表
            feed_ids: Feed ID列表，用于关联多个Feed (必填)
            invocation_id: 关联的调用ID
            raw_data: 原始数据（JSON格式）
            summary: 总结内容
        """
        session = self.db.get_session()
        try:
            # 检查feed_ids是否有值
            if not feed_ids:
                logger.warning("没有提供feed_ids，无法关联Feed")
                return None
                
            # 创建新条目
            entry = RSSEntry(
                guid=str(uuid.uuid4()),  # 生成一个唯一的GUID
                title=title,
                content=description,
                links=[link] if link else [],
                published_at=published_date,
                raw_data=raw_data
            )
            
            # 先将entry添加到session中
            session.add(entry)
            
            # 初始化feeds列表
            if not hasattr(entry, 'feeds') or entry.feeds is None:
                entry.feeds = []
                
            # 关联所有提供的feed
            valid_feed_count = 0
            for feed_id in feed_ids:
                if not feed_id:
                    logger.warning("发现空的feed_id，跳过")
                    continue
                    
                # 使用with session.no_autoflush来避免自动刷新
                with session.no_autoflush:
                    feed = session.query(RSSFeed).get(feed_id)
                    if feed:
                        # 直接将feed添加到entry.feeds列表中
                        entry.feeds.append(feed)
                        valid_feed_count += 1
                        logger.info(f"关联Feed: {feed.name} (ID: {feed.id})")
                    else:
                        logger.warning(f"Feed ID {feed_id} 不存在，跳过关联")
            
            # 如果没有有效的feed关联，记录警告
            if valid_feed_count == 0:
                logger.warning(f"没有成功关联任何Feed，提供的feed_ids: {feed_ids}")
            
            # 如果有总结，设置总结
            if summary:
                entry.set_summary(summary)
            
            # 如果有调用ID，设置关联
            if invocation_id:
                entry.invocation_id = invocation_id
            
            # 提交事务
            session.commit()
            logger.info(f"保存RSS条目: {title}, 关联Feed数: {len(entry.feeds)}")
            return entry
        except Exception as e:
            logger.error(f"保存RSS条目失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_entries_by_invocation(self, invocation_id: str) -> List[RSSEntry]:
        """根据调用ID获取RSS条目
        
        Args:
            invocation_id: 调用ID
            
        Returns:
            List[RSSEntry]: RSS条目列表
        """
        return self.session.query(RSSEntry).filter(RSSEntry.invocation_id == invocation_id).all()