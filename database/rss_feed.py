from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum, Table, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from .base import Base
from .rss_entry import entry_feed_association  # 导入中间表


# 修改RSSFeed类中的关系定义
class RSSFeed(Base):
    """RSS Feed模型，用于存储RSS源信息"""
    __tablename__ = "rss_feeds"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    
    # 基本信息
    name = Column(String(255), nullable=False, comment='Feed名称')
    url = Column(String(1024), nullable=False, comment='Feed URL')
    description = Column(Text, nullable=True, comment='Feed描述')
    category = Column(String(50), nullable=True, comment='Feed分类')
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_fetch_at = Column(DateTime(6), nullable=True, comment='最后一次获取时间')
    created_at = Column(DateTime(6), default=datetime.now, comment='创建时间')
    
    # 关系 - 修改为使用中间表的多对多关系
    entries = relationship("RSSEntry", secondary=entry_feed_association, back_populates="feeds")
    
    # 使用AgentRSSFeed作为关联
    feed = relationship("AgentRSSFeed", back_populates="feed")
    
    # 移除直接的多对多关系
    # agents = relationship("Agent", secondary=agent_feed_association, back_populates="feeds")
    
    
    @classmethod
    def init_default_feeds(cls, session):
        """初始化默认的RSS Feed数据"""
        # 默认Feed数据
        default_feeds = [
            {
                "feed_url": "https://www.wired.com/feed/",
                "title": "Wired",
                "category": "tech",
                "language": "en"
            },
            {
                "feed_url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
                "title": "BBC科技",
                "category": "tech",
                "language": "en"
            },
            {
                "feed_url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
                "title": "BBC足球",
                "category": "football",
                "language": "en"
            },
            {
                "feed_url": "https://www.espn.com/espn/rss/soccer/news",
                "title": "ESPN足球",
                "category": "football",
                "language": "en"
            },
            {
                "feed_url": "https://feeds.bbci.co.uk/news/business/rss.xml",
                "title": "BBC金融",
                "category": "business",
                "language": "en"
            },
            {
                "feed_url": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
                "title": "CNBC金融",
                "category": "business",
                "language": "en"
            }
        ]
        
        # 检查并添加默认Feed
        for feed_data in default_feeds:
            # 检查是否已存在
            existing_feed = session.query(cls).filter(
                cls.name == feed_data["title"],
                cls.url == feed_data["feed_url"]
            ).first()
            
            if not existing_feed:
                # 创建新Feed
                category_value = feed_data["category"]
                # category_enum = None
                
                # # 将字符串类别转换为枚举值
                # if category_value == "tech":
                #     category_enum = FeedCategory.TECH
                # elif category_value == "football":
                #     category_enum = FeedCategory.FOOTBALL
                # elif category_value == "business":
                #     category_enum = FeedCategory.BUSINESS
                # else:
                #     category_enum = FeedCategory.OTHER
                
                # 直接使用枚举对象，而不是枚举名称
                new_feed = cls(
                    id=str(uuid.uuid4()),
                    name=feed_data["title"],
                    url=feed_data["feed_url"],
                    description=f"{feed_data['title']} RSS Feed",
                    category=category_value  # 使用枚举对象
                )
                session.add(new_feed)
        
        # 提交事务
        session.commit()
    