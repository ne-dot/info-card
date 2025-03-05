from models.user import User
from utils.logger import setup_logger
from utils.password_utils import hash_password, verify_password
from datetime import datetime
import uuid

logger = setup_logger('user_dao')

class UserDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, username, email, password):
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if await self.get_user_by_username(username):
                logger.warning(f"用户名已存在: {username}")
                return None, "用户名已存在"
            
            # 检查邮箱是否已存在
            if await self.get_user_by_email(email):
                logger.warning(f"邮箱已存在: {email}")
                return None, "邮箱已存在"
            
            # 哈希密码
            password_hash = hash_password(password)
            
            # 创建用户对象
            user_id = str(uuid.uuid4())
            user = User(user_id=user_id, username=username, email=email, password_hash=password_hash)
            
            # 创建数据库模型
            from database.models import UserModel
            user_model = UserModel(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=datetime.now(),
                is_active=True
            )
            
            session = self.db.get_session()
            try:
                session.add(user_model)
                session.commit()
                logger.info(f"创建用户成功: {username}")
                return user, None
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return None, f"创建用户失败: {str(e)}"

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
                        created_at=user_model.created_at,
                        last_login=user_model.last_login
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
                        created_at=user_model.created_at,
                        last_login=user_model.last_login
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
                    user_model.last_login = datetime.now()
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