import jwt
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import setup_logger
import os

logger = setup_logger('jwt_utils')

# 从环境变量获取密钥，如果不存在则使用默认值
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, int(expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60)

def create_refresh_token(data: dict):
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token):
    """解码JWT令牌"""
    try:
        # 确保使用与创建令牌时相同的密钥和算法
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning(f"令牌已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效令牌: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"解码令牌时发生错误: {str(e)}")
        return None