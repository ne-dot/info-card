from dao.user_dao import UserDAO
from utils.password_utils import verify_password
from utils.jwt_utils import create_access_token, create_refresh_token, decode_token
from utils.logger import setup_logger
from models.user import User, UserResponse
import re
from utils.response_utils import ErrorCode
from utils.i18n_utils import get_text

logger = setup_logger('auth_service')

class AuthService:
    def __init__(self, db):
        self.user_dao = UserDAO(db)

    async def register(self, username, email, password, lang='en'):
        """注册新用户"""
        try:
            # 1. 检查用户名是否唯一
            existing_user = await self.user_dao.get_user_by_username(username)
            if existing_user:
                logger.warning(f"用户名已存在: {username}")
                return None, get_text("username_exists", lang), ErrorCode.USER_ALREADY_EXISTS
            
            # 2. 验证邮箱格式
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                logger.warning(f"邮箱格式无效: {email}")
                return None, get_text("invalid_email", lang), ErrorCode.INVALID_EMAIL
            
            # 检查邮箱是否已被使用
            existing_email = await self.user_dao.get_user_by_email(email)
            logger.warning(f"邮箱检查: {existing_email}")
            if existing_email:
                logger.warning(f"邮箱已被使用: {email}")
                return None, get_text("email_exists", lang), ErrorCode.EMAIL_ALREADY_EXISTS

            # 3. 验证密码长度和格式
            if not password or password.strip() == "":
                logger.warning("密码不能为空")
                return None, get_text("password_empty", lang), ErrorCode.INVALID_PASSWORD
                      
            user, error = await self.user_dao.create_user(username, email, password)
            if error:
                return None, error, ErrorCode.UNKNOWN_ERROR
            
            # 创建用户响应对象
            user_response = UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                last_login=user.last_login
            )
            
            return user_response, None, None
        except Exception as e:
            logger.error(f"注册失败: {str(e)}")
            return None, f"{get_text('register_failed', lang)}: {str(e)}", ErrorCode.UNKNOWN_ERROR

    async def login(self, username_or_email, password, lang='en'):
        """用户登录（支持用户名或邮箱）"""
        try:
            # 尝试通过用户名获取用户
            user = await self.user_dao.get_user_by_username(username_or_email)
            
            # 如果用户名不存在，尝试通过邮箱获取用户
            if not user:
                user = await self.user_dao.get_user_by_email(username_or_email)
                
            if not user:
                logger.warning(f"用户不存在: {username_or_email}")
                return None, get_text("invalid_credentials", lang)
            
            # 验证密码
            if not verify_password(password, user.password_hash):
                logger.warning(f"密码错误: {username_or_email}")
                return None, get_text("invalid_credentials", lang)
            
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
            return None, f"{get_text('login_failed', lang)}: {str(e)}"

    async def refresh_token(self, refresh_token, lang='en'):
        """刷新访问令牌"""
        try:
            # 解码刷新令牌
            payload = decode_token(refresh_token)
            if not payload:
                return None, get_text("invalid_refresh_token", lang)
            
            user_id = payload.get("sub")
            username = payload.get("username")
            
            # 验证用户是否存在
            user = await self.user_dao.get_user_by_id(user_id)
            if not user:
                return None, get_text("user_not_found", lang)
            
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
            return None, f"{get_text('refresh_token_failed', lang)}: {str(e)}"

    async def get_current_user(self, token, lang='en'):
        """获取当前用户"""
        try:
            # 解码令牌
            payload = decode_token(token)
            if not payload:
                return None, get_text("invalid_token", lang)
            
            user_id = payload.get("sub")
            
            # 获取用户
            user = await self.user_dao.get_user_by_id(user_id)
            if not user:
                return None, get_text("user_not_found", lang)
            
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
            return None, f"{get_text('get_user_failed', lang)}: {str(e)}"