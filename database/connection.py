from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from .base import Base
from .user_models import UserModel
from .agent import Agent
from .rss_feed import RSSFeed
import uuid
from utils.password_utils import hash_password

class Database:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def get_session(self):
        return self.Session()
    
    def init_database(self):
        """初始化数据库"""
        # 创建所有表
        Base.metadata.create_all(self.engine)
        
        # 获取会话
        session = self.get_session()
        
        try:
            # 检查是否已有管理员用户
            admin_user = session.query(UserModel).filter_by(
                auth_type='admin', 
                email='admin1@example.com'
            ).first()

            # 初始化默认RSS订阅源
            RSSFeed.init_default_feeds(session)
            
            # 如果没有管理员用户，创建一个
            if not admin_user:
                admin_user = UserModel(
                    id=str(uuid.uuid4()),
                    auth_type='admin',
                    email='admin2@example.com',
                    username='admin2',
                    is_email_verified=True,
                    password_hash=hash_password('admin123')  # 实际应用中应该使用加密后的密码
                )
                session.add(admin_user)
                session.flush()
                
                # 初始化默认Agent
                Agent.init_default_agents(session, admin_user.id)
                
                session.commit()
                print("已创建管理员用户和默认Agent")
            else:
                # 检查是否已有默认Agent
                agents = session.query(Agent).filter_by(user_id=admin_user.id).all()
                if not agents:
                    # 初始化默认Agent
                    Agent.init_default_agents(session, admin_user.id)
                    session.commit()
                    print("已创建默认Agent")
                else:
                    print("数据库已初始化")
            
            
        
        except Exception as e:
            session.rollback()
            print(f"初始化数据库时出错: {e}")
        finally:
            session.close()
    
    def close(self):
        self.Session.remove()