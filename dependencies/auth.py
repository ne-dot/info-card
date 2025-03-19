from fastapi import HTTPException, Header
from typing import Optional
from models.user import UserResponse
from services.user_service import UserService
from utils.logger import setup_logger

logger = setup_logger('auth_dependency')

# 全局变量存储用户服务实例
user_service = None

def init_dependency(service: UserService):
    """初始化依赖，设置全局用户服务实例"""
    global user_service
    user_service = service
    logger.info("认证依赖初始化完成")

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