from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum, Integer, Float, JSON, DateTime
from sqlalchemy.orm import relationship
import time
import uuid
from .base import Base
from datetime import datetime

class RSSFeed(Base):
    """RSS订阅源模型，用于存储RSS源信息"""
    __tablename__ = "rss_feeds"
    
    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False, comment='UUIDv7')
    
    # 基本信息
    feed_url = Column(String(512), nullable=False, unique=True, comment='RSS源地址')
    title = Column(String(255), nullable=False, comment='源标题')
    category = Column(Enum('news', 'sports', 'football', 'tech', 'custom', 'business', name='category_enum'), default='news')
    language = Column(String(2), default='zh', comment='ISO语言代码')
    
    # 缓存控制
    etag = Column(String(128), nullable=True, comment='HTTP缓存标识')
    last_modified = Column(DateTime(6), nullable=True, comment='最后更新时间戳')
    
    # 健康状态
    health_status = Column(JSON, nullable=True, comment='健康状态信息')
    
    # 审计字段
    created_at = Column(DateTime(6), default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime(6), default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    entries = relationship("RSSEntry", back_populates="feed", cascade="all, delete-orphan")
    agent_feeds = relationship("AgentRSSFeed", back_populates="feed", cascade="all, delete-orphan")
    
    def __init__(self, feed_url, title, category='news', language='zh', etag=None, last_modified=None):
        self.id = str(uuid.uuid4())
        self.feed_url = feed_url
        self.title = title
        self.category = category
        self.language = language
        self.etag = etag
        self.last_modified = last_modified
        self.health_status = {
            "failure_count": 0,
            "last_success": None,
            "avg_interval": 3600
        }
    
    def update_health_status(self, success=True):
        """更新RSS源的健康状态
        
        Args:
            success: 是否成功获取RSS源
        """
        if not self.health_status:
            self.health_status = {
                "failure_count": 0,
                "last_success": None,
                "avg_interval": 3600
            }
        
        if success:
            # 成功获取RSS源
            now = datetime.now().isoformat()
            last_success = self.health_status.get("last_success")
            
            # 计算平均间隔时间
            if last_success:
                last_success_time = datetime.fromisoformat(last_success)
                interval = (datetime.now() - last_success_time).total_seconds()
                avg_interval = self.health_status.get("avg_interval", 3600)
                # 更新平均间隔 (加权平均)
                self.health_status["avg_interval"] = (avg_interval * 0.7) + (interval * 0.3)
            
            self.health_status["last_success"] = now
            self.health_status["failure_count"] = 0
        else:
            # 获取失败
            self.health_status["failure_count"] = self.health_status.get("failure_count", 0) + 1
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            "id": self.id,
            "feed_url": self.feed_url,
            "title": self.title,
            "category": self.category,
            "language": self.language,
            "etag": self.etag,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "health_status": self.health_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    # 在 RSSFeed 类中添加初始化方法
    
    @classmethod
    def init_default_feeds(cls, session):
        """初始化默认的RSS订阅源
        
        Args:
            session: 数据库会话
            
        Returns:
            list: 创建的RSS订阅源列表
        """
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
        
        created_feeds = []
        
        for feed_data in default_feeds:
            # 检查是否已存在
            existing = session.query(cls).filter(cls.feed_url == feed_data["feed_url"]).first()
            if existing:
                created_feeds.append(existing)
                continue
                
            # 创建新的RSS源
            feed = cls(
                feed_url=feed_data["feed_url"],
                title=feed_data["title"],
                category=feed_data["category"],
                language=feed_data["language"]
            )
            session.add(feed)
            created_feeds.append(feed)
        
        # 提交事务
        session.commit()
        
        return created_feeds