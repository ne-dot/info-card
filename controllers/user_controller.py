from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth_service import AuthService
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode

router = APIRouter()
logger = setup_logger('user_controller')
auth_service = None

def init_controller(service: AuthService):
    global auth_service
    auth_service = service

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """注册新用户"""
    logger.info(f"接收到注册请求: {user_data.username}, {user_data.email}")
    try:
        user, error, error_code = await auth_service.register(
            user_data.username, 
            user_data.email, 
            user_data.password
        )
        if error:
            logger.error(f"注册失败: {error}")
            return error_response(error, error_code)
        
        logger.info(f"注册成功: {user_data.username}")
        return success_response(user.dict(), "注册成功")
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        return error_response(f"注册失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """用户登录（支持用户名或邮箱）"""
    try:
        token, error = await auth_service.login(
            login_data.username_or_email,  # 修改这里，使用新的属性名
            login_data.password
        )
        if error:
            logger.warning(f"登录失败: {error}")
            return error_response(error, ErrorCode.LOGIN_FAILED)
        
        return success_response(token, "登录成功")
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return error_response(f"登录失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Header(...)):
    """刷新访问令牌"""
    try:
        token, error = await auth_service.refresh_token(refresh_token)
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
    
    user, error = await auth_service.get_current_user(token)
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return user

@router.get("/me")
async def get_user_info(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        return success_response(current_user.dict(), "获取用户信息成功")
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return error_response(f"获取用户信息失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)