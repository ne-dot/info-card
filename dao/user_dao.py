from database.user_models import UserModel  
from models.user import User
from sqlalchemy import select
import uuid
import time
from utils.password_utils import hash_password
from datetime import datetime

class UserDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, username, email, password):
        """创建新用户"""
        try:
            # 获取会话
            session = self.db.get_session()
            try:
                # 创建用户模型
                now = int(time.time())
                user_model = UserModel(
                    id=str(uuid.uuid4()),
                    auth_type='email',
                    auth_id=email,
                    email=email,
                    username=username,
                    password_hash=password,
                    created_at=now,
                    updated_at=now,
                    last_login_at=now,
                    account_status='active',
                    is_deleted=False
                )
                
                # 添加到数据库
                session.add(user_model)
                session.commit()
                
                # 转换为业务模型
                return User(
                    user_id=user_model.id,
                    username=user_model.username,
                    email=user_model.email,
                    password_hash=user_model.password_hash,
                    created_at=user_model.created_at,
                    last_login=user_model.last_login_at,
                    is_anonymous=False
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
            # 如果没有提供匿名ID，生成一个
            if not anonymous_id:
                anonymous_id = str(uuid.uuid4())
            
            # 哈希密码
            password_hash = hash_password(password)
            
            # 获取会话
            session = self.db.get_session()
            try:
                # 创建用户模型
                now = int(time.time())
                user_model = UserModel(
                    id=str(uuid.uuid4()),
                    auth_type='anonymous',
                    auth_id=anonymous_id,
                    username=username,
                    password_hash=password_hash,
                    created_at=now,
                    updated_at=now,
                    last_login_at=now,
                    account_status='active',
                    is_deleted=False
                )
                
                # 添加到数据库
                session.add(user_model)
                session.commit()
                
                # 转换为业务模型
                return User(
                    user_id=user_model.id,
                    username=user_model.username,
                    email=None,
                    password_hash=user_model.password_hash,
                    created_at=user_model.created_at,
                    last_login=user_model.last_login_at,
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
                # 查询条件改为 auth_type='anonymous' 且 auth_id=anonymous_id
                user_model = session.query(UserModel).filter(
                    UserModel.auth_type == 'anonymous',
                    UserModel.auth_id == anonymous_id
                ).first()
                
                if user_model:
                    return User(
                        user_id=user_model.id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,  # 直接使用整数时间戳
                        last_login=user_model.last_login_at,  # 直接使用整数时间戳
                        is_anonymous=True
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
                user_model = session.query(UserModel).filter(UserModel.username == username).first()
                if user_model:
                    return User(
                        user_id=user_model.id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,  # 直接使用整数时间戳
                        last_login=user_model.last_login_at,  # 直接使用整数时间戳
                        is_anonymous=(user_model.auth_type == 'anonymous')
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_user_by_email(self, email):
        """通过邮箱获取用户"""
        try:
            session = self.db.get_session()
            try:
                user_model = session.query(UserModel).filter(UserModel.email == email).first()
                if user_model:
                    return User(
                        user_id=user_model.id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,  # 直接使用整数时间戳
                        last_login=user_model.last_login_at,  # 直接使用整数时间戳
                        is_anonymous=(user_model.auth_type == 'anonymous')
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def get_user_by_id(self, user_id):
        """通过用户ID获取用户"""
        try:
            session = self.db.get_session()
            try:
                user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
                if user_model:
                    return User(
                        user_id=user_model.id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,  # 直接使用整数时间戳
                        last_login=user_model.last_login_at,  # 直接使用整数时间戳
                        is_anonymous=(user_model.auth_type == 'anonymous')
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def update_last_login(self, user_id):
        """更新用户最后登录时间"""
        try:
            session = self.db.get_session()
            try:
                # 查询条件改为 id 字段
                user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
                if user_model:
                    # 使用时间戳
                    user_model.last_login_at = int(time.time())
                    session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('user_dao')
            logger.error(f"更新登录时间失败: {str(e)}")
            return False

    async def update_user(self, user_id, username=None, email=None, password_hash=None, is_anonymous=None):
        """更新用户信息"""
        try:
            session = self.db.get_session()
            try:
                # 查询条件改为 id 字段
                user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
                if user_model:
                    # 更新用户信息
                    if username is not None:
                        user_model.username = username
                    
                    if email is not None:
                        user_model.email = email
                        # 如果是邮箱用户，同时更新 auth_id
                        if user_model.auth_type == 'email':
                            user_model.auth_id = email
                    
                    if password_hash is not None:
                        user_model.password_hash = password_hash
                    
                    if is_anonymous is not None:
                        # 更新认证类型
                        user_model.auth_type = 'anonymous' if is_anonymous else 'email'
                        # 如果从匿名转为非匿名，需要设置 auth_id 为邮箱
                        if not is_anonymous and user_model.email:
                            user_model.auth_id = user_model.email
                    
                    # 更新时间戳
                    user_model.updated_at = int(time.time())
                    
                    # 提交更改
                    session.commit()
                    
                    # 返回更新后的用户对象
                    return User(
                        user_id=user_model.id,
                        username=user_model.username,
                        email=user_model.email,
                        password_hash=user_model.password_hash,
                        created_at=user_model.created_at,
                        last_login=user_model.last_login_at,
                        is_anonymous=(user_model.auth_type == 'anonymous')
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

    async def get_user_by_email_and_type(self, email, auth_type):
        """根据邮箱和认证类型获取用户"""
        try:
            session = self.db.get_session()
            user = session.query(UserModel).filter(
                UserModel.email == email,
                UserModel.auth_type == auth_type
            ).first()
            return user
        except Exception as e:
            logger.error(f"根据邮箱和类型获取用户失败: {str(e)}")
            return None
        finally:
            session.close()