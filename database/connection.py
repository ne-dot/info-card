from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from utils.logger import setup_logger

logger = setup_logger('database')

Base = declarative_base()

class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        
        logger.info(f"数据库引擎初始化: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    def init_database(self):
        """初始化数据库表"""
        try:
            from database.models import Base
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建数据库表失败: {str(e)}")
            return False
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("数据库连接已关闭")