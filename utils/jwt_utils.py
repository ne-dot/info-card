import jwt
from datetime import datetime, timedelta
from utils.logger import setup_logger
import os

logger = setup_logger('jwt_utils')

# 从环境变量获取密钥，如果不存在则使用默认值
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    """创建访问令牌"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt, ACCESS_TOKEN_EXPIRE_MINUTES * 60
    except Exception as e:
        logger.error(f"创建访问令牌失败: {str(e)}")
        raise e

def create_refresh_token(data: dict):
    """创建刷新令牌"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建刷新令牌失败: {str(e)}")
        raise e

def decode_token(token: str):
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("令牌已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效令牌: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"解码令牌失败: {str(e)}")
        return None