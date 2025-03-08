from models.user import User
from utils.logger import setup_logger
from utils.password_utils import hash_password, verify_password
import time
import uuid

logger = setup_logger('user_dao')

class UserDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_user(self, username, email, password):
        """创建新用户"""
        try:
            # 哈希密码
            password_hash = hash_password(password)
            
            # 创建用户对象
            user_id = str(uuid.uuid4())
            current_timestamp = int(time.time())
            user = User(
                user_id=user_id, 
                username=username, 
                email=email, 
                password_hash=password_hash,
                created_at=current_timestamp  # 确保传递时间戳
            )
            
            # 创建数据库模型
            from database.models import UserModel
            user_model = UserModel(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=current_timestamp,  # 使用时间戳
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