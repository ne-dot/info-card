from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth_service import AuthService
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger('user_controller')
auth_service = None

def init_controller(service: AuthService):
    global auth_service
    auth_service = service

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """注册新用户"""
    logger.info(f"接收到注册请求: {user_data.username}, {user_data.email}, {user_data.password}")
    try:
        user, error = await auth_service.register(
            user_data.username, 
            user_data.email, 
            user_data.password
        )
        if error:
            logger.error(f"注册失败: {error}")
            raise HTTPException(status_code=400, detail=error)
        logger.info(f"注册成功: {user_data.username}")
        return user
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """用户登录"""
    try:
        token, error = await auth_service.login(
            login_data.username,
            login_data.password
        )
        if error:
            raise HTTPException(status_code=401, detail=error)
        return token
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="认证方案无效")
    
    user, error = await auth_service.get_current_user(token)
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_user_info(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user