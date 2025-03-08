from typing import Any, Dict, Optional, Union
from fastapi.responses import JSONResponse

class ResponseModel:
    """统一响应模型"""
    def __init__(
        self, 
        success: bool = True, 
        data: Any = None, 
        message: str = "操作成功", 
        error_code: Optional[int] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.error_code = error_code
    
    def dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "success": self.success,
            "message": self.message
        }
        
        if self.data is not None:
            result["data"] = self.data
            
        if self.error_code is not None:
            result["error_code"] = self.error_code
            
        return result

def success_response(data: Any = None, message: str = "操作成功") -> JSONResponse:
    """成功响应"""
    return JSONResponse(content=ResponseModel(success=True, data=data, message=message).dict())

def error_response(message: str, error_code: int = 400, data: Any = None) -> JSONResponse:
    """错误响应"""
    return JSONResponse(content=ResponseModel(success=False, data=data, message=message, error_code=error_code).dict())

# 错误码定义
class ErrorCode:
    """错误码定义"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_PARAMS = 1001
    
    # 用户相关错误 (2000-2999)
    USER_NOT_FOUND = 2000
    USER_ALREADY_EXISTS = 2001
    INVALID_USERNAME = 2002
    INVALID_EMAIL = 2003
    INVALID_PASSWORD = 2004
    EMAIL_ALREADY_EXISTS = 2005
    LOGIN_FAILED = 2006
    
    # 认证相关错误 (3000-3999)
    UNAUTHORIZED = 3000
    INVALID_TOKEN = 3001
    TOKEN_EXPIRED = 3002
    
    # 搜索相关错误 (4000-4999)
    SEARCH_FAILED = 4000