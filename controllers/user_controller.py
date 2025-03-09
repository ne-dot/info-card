from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from services.user_service import UserService
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from utils.i18n_utils import get_text
from fastapi import Request

router = APIRouter()
logger = setup_logger('user_controller')
user_service = None

def init_controller(service: UserService):
    global user_service
    user_service = service

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, request: Request):
    """用户登录（支持用户名或邮箱）"""
    try:
        # 从请求中获取语言设置，默认为英文
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        
        token, error = await user_service.login(
            login_data.username_or_email,
            login_data.password,
            lang  # 传递语言参数
        )
        if error:
            logger.warning(f"登录失败: {error}")
            return error_response(error, ErrorCode.LOGIN_FAILED)
        
        return success_response(token, get_text("login_success", lang))
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        return error_response(f"{get_text('login_failed', lang)}: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Header(...)):
    """刷新访问令牌"""
    try:
        token, error = await user_service.refresh_token(refresh_token)
        if error:
            raise HTTPException(status_code=401, detail=error)
        return token
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_current_user(authorization: Optional[str] = Header(None)):
    """获取当前用户，用于依赖注入"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    # More robust splitting of the authorization header
    parts = authorization.split()
    if len(parts) < 2:
        raise HTTPException(status_code=401, detail="认证格式无效")
    
    scheme = parts[0]
    token = ' '.join(parts[1:])  # Join all remaining parts as the token
    
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="认证方案无效")
    
    user, error = await user_service.get_current_user(token)
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return user

@router.get("/me")
async def get_user_info(request: Request, current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        # 从请求中获取语言设置，默认为英文
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        logger.info(f"当前语言: {lang}")
        return success_response(current_user.dict(), get_text("get_user_success", lang))
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        return error_response(f"{get_text('get_user_failed', lang)}: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.post("/anonymous-login", response_model=TokenResponse)
async def anonymous_login(request: Request):
    """匿名用户登录"""
    try:
        # 从请求中获取语言设置，默认为英文
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        
        # 创建匿名用户
        result, error, error_code = await user_service.create_anonymous_user(lang)
        if error:
            # 增加更详细的日志记录
            logger.warning(f"匿名登录失败: {error}, 错误码: {error_code}")
            return error_response(error, error_code)
        
        return success_response(result, get_text("anonymous_login_success", lang))
    except Exception as e:
        # 记录详细的异常信息
        import traceback
        logger.error(f"匿名登录失败，详细异常: {str(e)}")
        logger.error(traceback.format_exc())
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        return error_response(f"{get_text('anonymous_login_failed', lang)}: {str(e)}", ErrorCode.ANONYMOUS_LOGIN_FAILED)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request):
    """注册新用户，支持从匿名用户转换"""
    logger.info(f"接收到注册请求: {user_data.username}, {user_data.email}")
    try:
        # 从请求中获取语言设置，默认为英文
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        
        # 从请求头中获取匿名ID（如果有）
        anonymous_id = request.headers.get("X-Anonymous-ID")
        
        user, error, error_code = await user_service.register(
            user_data.username, 
            user_data.email, 
            user_data.password,
            lang,
            anonymous_id
        )
        if error:
            logger.error(f"注册失败: {error}")
            return error_response(error, error_code)
        
        logger.info(f"注册成功: {user_data.username}")
        return success_response(user.dict(), get_text("register_success", lang))
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        return error_response(f"{get_text('register_failed', lang)}: {str(e)}", ErrorCode.UNKNOWN_ERROR)
