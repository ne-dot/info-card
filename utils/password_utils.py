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
        logger.info(f"生成密码哈希: 原始密码长度={len(password)}, 哈希结果={hashed_str}")
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
        
        # 添加调试日志
        logger.info(f"验证密码: 明文密码={plain_password}, 明文长度={len(plain_password)}, 哈希长度={len(hashed_password)}")
        
        # 尝试重新哈希明文密码，看看结果
        test_hash = bcrypt.hashpw(plain_password_bytes, hashed_password_bytes[:29])
        logger.info(f"测试哈希: {test_hash.decode('utf-8')}")
        logger.info(f"期望哈希: {hashed_password}")
        
        result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
        logger.info(f"密码验证结果: {result}")
        return result
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False