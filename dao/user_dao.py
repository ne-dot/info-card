from database.models import UserModel  
from models.user import User
from sqlalchemy import select
import uuid
import time
from utils.password_utils import hash_password

class UserDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, username, email, password):
        """创建新用户，支持匿名用户标记"""
        try:
            user_id = str(uuid.uuid4())
            now = int(time.time())
            
            # 获取会话
            session = self.db.get_session()
            try:
                # 创建用户模型
                user_model = UserModel(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=hash_password(password),
                    created_at=now,
                    last_login=now,
                    is_anonymous=False,
                    anonymous_id=None 
                )
                
                # 添加到数据库
                session.add(user_model)
                session.commit()
                
                # 转换为业务模型
                return User(
                    user_id=user_model.user_id,
                    username=user_model.username,
                    email=user_model.email,
                    password_hash=user_model.password_hash,
                    created_at=user_model.created_at,
                    last_login=user_model.last_login,
                    is_anonymous=user_model.is_anonymous
                ), None
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"创建用户失败: {str(e)}")
            return None, str(e)
    
    async def create_anonymous_user(self, username, password, anonymous_id=None):
        """创建匿名用户"""
        try:
            user_id = str(uuid.uuid4())
            now = int(time.time())
            
            # 哈希密码
            password_hash = hash_password(password)
            
            # 获取会话
            session = self.db.get_session()
            try:
                # 创建用户模型
                user_model = UserModel(
                    user_id=user_id,
                    username=username,
                    email=None,  # 匿名用户没有邮箱
                    password_hash=password_hash,
                    created_at=now,
                    last_login=now,
                    is_anonymous=True,
                    anonymous_id=anonymous_id
                )
                
                # 添加到数据库
                session.add(user_model)
                session.commit()
                
                # 转换为业务模型
                return User(
                    user_id=user_model.user_id,
                    username=user_model.username,
                    email=user_model.email,
                    password_hash=user_model.password_hash,
                    created_at=user_model.created_at,
                    last_login=user_model.last_login,
                    is_anonymous=True
                )
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"创建匿名用户失败: {str(e)}")
            return None
    
    async def get_user_by_anonymous_id(self, anonymous_id):
        """通过匿名ID获取用户"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.anonymous_id == anonymous_id).first()
                if user_model:
                    return User(
                        user_id=user_model.user_id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,
                        last_login=user_model.last_login,
                        is_anonymous=user_model.is_anonymous
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"通过匿名ID获取用户失败: {str(e)}")
            return None
    
    async def get_user_by_username(self, username):
        """通过用户名获取用户"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.username == username).first()
                if user_model:
                    return User(
                        user_id=user_model.user_id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,
                        last_login=user_model.last_login
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_user_by_email(self, email):
        """通过邮箱获取用户"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.email == email).first()
                if user_model:
                    return User(
                        user_id=user_model.user_id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        # 移除 created_at 参数，或者确保 User 类支持这个参数
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_user_by_id(self, user_id):
        """通过用户ID获取用户"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user_model:
                    return User(
                        user_id=user_model.user_id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        # 移除 created_at 和 last_login 参数
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def update_last_login(self, user_id):
        """更新用户最后登录时间"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user_model:
                    user_model.last_login = int(time.time())  # 使用时间戳
                    session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新登录时间失败: {str(e)}")
            return False

    async def update_user(self, user_id, username=None, email=None, password_hash=None, is_anonymous=None):
        """更新用户信息，支持更新匿名状态"""
        try:
            session = self.db.get_session()
            try:
                from database.models import UserModel
                user_model = session.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user_model:
                    # 更新用户信息
                    if username is not None:
                        user_model.username = username
                    if email is not None:
                        user_model.email = email
                    if password_hash is not None:
                        user_model.password_hash = password_hash
                    if is_anonymous is not None:
                        user_model.is_anonymous = is_anonymous
                    
                    # 提交更改
                    session.commit()
                    
                    # 返回更新后的用户对象
                    return User(
                        user_id=user_model.user_id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,
                        last_login=user_model.last_login,
                        is_anonymous=user_model.is_anonymous
                    )
                return None
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"更新用户失败: {str(e)}")
            return None