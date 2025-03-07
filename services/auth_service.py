from dao.user_dao import UserDAO
from utils.password_utils import verify_password
from utils.jwt_utils import create_access_token, create_refresh_token, decode_token
from utils.logger import setup_logger
from models.user import User, UserResponse
import re

logger = setup_logger('auth_service')

class AuthService:
    def __init__(self, db):
        self.user_dao = UserDAO(db)

    async def register(self, username, email, password):
        """注册新用户"""
        try:
            # 检查密码是否为空
            if not password or password.strip() == "":
                logger.warning("密码不能为空")
                return None, "密码不能为空"

            # 1. 检查用户名是否唯一
            existing_user = await self.user_dao.get_user_by_username(username)
            if existing_user:
                logger.warning(f"用户名已存在: {username}")
                return None, "用户名已存在，请选择其他用户名"
            
            # 2. 验证邮箱格式
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                logger.warning(f"邮箱格式无效: {email}")
                return None, "邮箱格式无效，请输入有效的邮箱地址"
            
            # 检查邮箱是否已被使用
            existing_email = await self.user_dao.get_user_by_email(email)
            if existing_email:
                logger.warning(f"邮箱已被使用: {email}")
                return None, "该邮箱已被注册，请使用其他邮箱"

            
            user, error = await self.user_dao.create_user(username, email, password)
            if error:
                return None, error
            
            # 创建用户响应对象
            user_response = UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                last_login=user.last_login
            )
            
            return user_response, None
        except Exception as e:
            logger.error(f"注册失败: {str(e)}")
            return None, f"注册失败: {str(e)}"

    async def login(self, username, password):
        """用户登录"""
        try:
            # 获取用户
            user = await self.user_dao.get_user_by_username(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                return None, "用户名或密码错误"
            
            # 验证密码
            if not verify_password(password, user.password_hash):
                logger.warning(f"密码错误: {username}")
                return None, "用户名或密码错误"
            
            # 更新最后登录时间
            await self.user_dao.update_last_login(user.user_id)
            
            # 创建令牌
            token_data = {"sub": user.user_id, "username": user.username}
            access_token, expires_in = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            # 返回令牌
            token_response = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "refresh_token": refresh_token
            }
            
            return token_response, None
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            return None, f"登录失败: {str(e)}"

    async def refresh_token(self, refresh_token):
        """刷新访问令牌"""
        try:
            # 解码刷新令牌
            payload = decode_token(refresh_token)
            if not payload:
                return None, "无效的刷新令牌"
            
            user_id = payload.get("sub")
            username = payload.get("username")
            
            # 验证用户是否存在
            user = await self.user_dao.get_user_by_id(user_id)
            if not user:
                return None, "用户不存在"
            
            # 创建新的访问令牌
            token_data = {"sub": user_id, "username": username}
            access_token, expires_in = create_access_token(token_data)
            
            # 返回新的访问令牌
            token_response = {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            }
            
            return token_response, None
        except Exception as e:
            logger.error(f"刷新令牌失败: {str(e)}")
            return None, f"刷新令牌失败: {str(e)}"

    async def get_current_user(self, token):
        """获取当前用户"""
        try:
            # 解码令牌
            payload = decode_token(token)
            if not payload:
                return None, "无效的令牌"
            
            user_id = payload.get("sub")
            
            # 获取用户
            user = await self.user_dao.get_user_by_id(user_id)
            if not user:
                return None, "用户不存在"
            
            # 创建用户响应对象
            user_response = UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                last_login=user.last_login
            )
            
            return user_response, None
        except Exception as e:
            logger.error(f"获取当前用户失败: {str(e)}")
            return None, f"获取当前用户失败: {str(e)}"