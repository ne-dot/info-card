import bcrypt
from utils.logger import setup_logger

logger = setup_logger('password_utils')

def hash_password(password):
    """对密码进行哈希处理"""
    try:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        hashed_str = hashed.decode('utf-8')
        # 只记录哈希成功，不记录具体密码信息
        logger.info("密码哈希生成成功")
        return hashed_str
    except Exception as e:
        logger.error(f"密码哈希失败: {str(e)}")
        raise e

def verify_password(plain_password, hashed_password):
    """验证密码"""
    try:
        # 确保输入是字符串
        if not plain_password or not hashed_password:
            logger.warning("密码验证失败: 密码为空")
            return False
            
        plain_password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        
        # 简化日志，只记录验证结果
        result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
        logger.info(f"密码验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False