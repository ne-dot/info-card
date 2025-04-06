from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from utils.jwt_utils import decode_token
from utils.logger import setup_logger

logger = setup_logger('auth_middleware')

# 不需要认证的路径列表
PUBLIC_PATHS = [
    "/api/users/login",
    "/api/users/register",
    "/api/suggestions",
    "/api/search",  # 添加搜索接口到公开路径
    "/"  # 根路径通常也是公开的
]

async def auth_middleware(request: Request, call_next):
    """认证中间件，验证请求中的令牌"""
    # 检查路径是否在公开路径列表中
    path = request.url.path
    if any(path.startswith(public_path) for public_path in PUBLIC_PATHS):
        # 如果是公开路径，直接放行
        return await call_next(request)
    
    # 获取认证头
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning("请求缺少认证头")
        raise HTTPException(status_code=401, detail="未认证")
    
    # 解析令牌
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            logger.warning(f"认证方案错误: {scheme}")
            raise HTTPException(status_code=401, detail="认证方案错误")
        
        # 解码令牌
        payload = decode_token(token)
        if not payload:
            logger.warning("无效的令牌")
            raise HTTPException(status_code=401, detail="无效的令牌")
        
        # 将用户信息添加到请求状态
        request.state.user = payload
        
        # 继续处理请求
        return await call_next(request)
    except Exception as e:
        logger.error(f"认证失败: {str(e)}")
        raise HTTPException(status_code=401, detail="认证失败")