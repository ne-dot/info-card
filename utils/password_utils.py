import bcrypt
from utils.logger import setup_logger

logger = setup_logger('password_utils')

def hash_password(password):
    """对密码进行哈希处理"""
    try:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"密码哈希失败: {str(e)}")
        raise e

def verify_password(plain_password, hashed_password):
    """验证密码"""
    try:
        plain_password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False