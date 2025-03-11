from typing import List, Optional
import time  
from sqlalchemy.orm import Session
from database.models import News, NewsSummary, NewsSummaryTrigger
from models.news import NewsItem
from utils.logger import setup_logger

logger = setup_logger('news_dao')

class NewsDAO:
    def __init__(self, db):
        self.db = db
    
    def save_news_to_db(self, news_items: List[NewsItem], trigger_id: int = None) -> List[int]:
        """将新闻保存到数据库，并可选关联到触发记录"""
        db_news_items = []
        session = self.db.get_session()
        try:
            # 如果提供了trigger_id，获取触发记录
            trigger = None
            if trigger_id:
                trigger = session.query(NewsSummaryTrigger).get(trigger_id)
                if not trigger:
                    logger.warning(f"找不到ID为{trigger_id}的触发记录")
            
            for item in news_items:
                # 检查新闻是否已存在
                existing_news = session.query(News).filter(News.link == item.link).first()
                
                if not existing_news:
                    # 创建新的新闻记录
                    db_news = News(
                        title=item.title,
                        description=item.description,
                        link=item.link,
                        published_date=item.published_date.isoformat(),
                        source=item.source,
                        categories=','.join(item.categories)
                    )
                    session.add(db_news)
                    session.flush()
                    db_news_items.append(db_news)
                else:
                    db_news_items.append(existing_news)
                
                # 如果有触发记录，关联新闻和触发记录
                if trigger:
                    news_to_link = existing_news if existing_news else db_news
                    
                    # 使用ORM方式检查关联是否已存在
                    from sqlalchemy.orm import contains_eager
                    exists = session.query(NewsSummaryTrigger).\
                        filter(NewsSummaryTrigger.id == trigger.id).\
                        filter(NewsSummaryTrigger.news_items.any(id=news_to_link.id)).\
                        first() is not None
                    
                    if not exists and news_to_link not in trigger.news_items:
                        trigger.news_items.append(news_to_link)
            
            # 提交事务
            session.commit()
            
            # 返回新闻ID列表而不是对象，避免会话关闭后的问题
            return [news.id for news in db_news_items]
        except Exception as e:
            logger.error(f"保存新闻到数据库失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_trigger_record(self, user_id: Optional[str], ip_address: str, trigger_type: str = "manual") -> dict:
        """创建触发记录，返回触发记录ID和对象"""
        session = self.db.get_session()
        try:
            trigger = NewsSummaryTrigger(
                trigger_type=trigger_type,
                user_id=user_id,
                ip_address=ip_address,
                created_at=int(time.time())
            )
            session.add(trigger)
            session.commit()  # 使用commit而不是flush，确保数据被保存
            
            # 返回触发记录ID和对象
            return {"id": trigger.id, "object": trigger}
        except Exception as e:
            logger.error(f"创建触发记录失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_summary_to_db(self, summary_content: str, language: str, 
                  trigger_id: int) -> NewsSummary:
        """保存摘要到数据库"""
        session = self.db.get_session()
        try:
            # 获取触发器对象
            trigger = session.query(NewsSummaryTrigger).get(trigger_id)
            if not trigger:
                logger.error(f"找不到ID为{trigger_id}的触发记录")
                raise ValueError(f"找不到ID为{trigger_id}的触发记录")
                
            # 创建摘要记录
            db_summary = NewsSummary(
                summary_content=summary_content,
                language=language,
                type="manual",
                created_at=int(time.time())
            )
            session.add(db_summary)
            session.flush()
            
            # 更新触发记录关联摘要
            trigger.summary_id = db_summary.id
            trigger.success = True
            
            session.commit()
            return db_summary
        except Exception as e:
            logger.error(f"保存摘要到数据库失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_trigger_failure(self, trigger_id: int, error_message: str) -> None:
        """更新触发记录为失败状态"""
        session = self.db.get_session()
        try:
            trigger = session.query(NewsSummaryTrigger).get(trigger_id)
            if trigger:
                trigger.success = False
                trigger.error_message = error_message
                session.commit()
            else:
                logger.error(f"找不到ID为{trigger_id}的触发记录")
        except Exception as e:
            logger.error(f"更新触发记录失败: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def save_failed_trigger(self, user_id: Optional[str], ip_address: str, error_message: str) -> None:
        """保存失败的触发记录"""
        session = self.db.get_session()
        try:
            trigger = NewsSummaryTrigger(
                trigger_type="manual",
                user_id=user_id,
                ip_address=ip_address,
                success=False,
                error_message=error_message,
                created_at=int(time.time())
            )
            session.add(trigger)
            session.commit()
        except Exception as e:
            logger.error(f"保存触发记录失败: {str(e)}")
            session.rollback()
        finally:
            session.close()