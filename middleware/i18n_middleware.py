from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utils.i18n_utils import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 从请求头中获取语言设置
        accept_language = request.headers.get("Accept-Language", DEFAULT_LANGUAGE)
        
        # 解析语言代码
        lang = accept_language.split(",")[0].strip()
        
        # 如果不支持该语言，使用默认语言
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        
        # 将语言设置添加到请求状态中
        request.state.lang = lang
        
        # 继续处理请求
        response = await call_next(request)
        return response