from database.rss_entry import RSSEntry
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from utils.logger import setup_logger
from database.rss_feed import RSSFeed
import uuid
from typing import List

logger = setup_logger('rss_entry_dao')

class RSSEntryDAO:
    def __init__(self, db):
        self.db = db
        self.session = db.get_session()
    
    def save_entry(self, title, description, link, published_date, source, categories, invocation_id=None, raw_data=None, summary=None):
        """保存RSS条目到数据库
        
        Args:
            title: 标题
            description: 描述
            link: 链接
            published_date: 发布日期
            source: 来源
            categories: 分类列表
            invocation_id: 关联的调用ID
            raw_data: 原始数据（JSON格式）
            summary: 总结内容
        """
        session = self.db.get_session()
        try:
            # 创建新条目
            entry = RSSEntry(
                guid=str(uuid.uuid4()),  # 生成一个唯一的GUID
                title=title,
                content=description,
                published_at=published_date,
                invocation_id=invocation_id,  # 直接设置invocation_id
                raw_data=raw_data
            )
            
            # 设置links
            if link:
                entry.links = {"main": link}
            
            # 先将entry添加到session中
            session.add(entry)
              
            # 如果有总结，设置总结
            if summary:
                entry.set_summary(summary)
            
            # 提交事务
            session.commit()
            logger.info(f"保存RSS条目: {title}")
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