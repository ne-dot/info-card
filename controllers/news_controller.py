from fastapi import APIRouter, Depends, Request, Query
from typing import List, Optional
from services.news_service import NewsService
from utils.response_utils import success_response, error_response, ErrorCode
from utils.logger import setup_logger
from config.settings import NEWS_SETTINGS

logger = setup_logger('news_controller')
router = APIRouter(tags=["新闻"], include_in_schema=True)

# 移除全局变量，使用依赖函数获取服务实例
def get_news_service(request: Request):
    return request.app.state.news_service

def init_controller(service):
    # 不再设置全局变量，而是在初始化时将服务实例存储到应用状态中
    # 这个函数会在app.py的lifespan中被调用
    pass

@router.get("/news/wired", response_model=None)
async def get_wired_news(
    limit: int = Query(NEWS_SETTINGS["default_news_limit"], ge=1, le=NEWS_SETTINGS["max_news_limit"]),
    news_service: NewsService = Depends(get_news_service)
):
    """获取Wired科技新闻"""
    try:
        news_items = await news_service.get_wired_news(limit=limit)
        news_items_dict = news_service.format_news_items(news_items)
            
        return success_response({
            "items": news_items_dict,
            "count": len(news_items_dict)
        })
    except Exception as e:
        logger.error(f"获取Wired新闻失败: {str(e)}")
        return error_response(f"获取新闻失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/news/summary", response_model=None)
async def get_news_summary(
    request: Request,
    news_service: NewsService = Depends(get_news_service)
):
    """获取近期科技新闻总结"""
    try:
        # 使用配置中的默认新闻数量
        limit = NEWS_SETTINGS["default_news_limit"]
        
        # 调用服务生成摘要 - 不再需要传递db参数，因为已经在service初始化时传入
        result = await news_service.generate_news_summary(request, None, limit)
        
        # 处理结果
        if "error" in result:
            return error_response(result["error"], getattr(ErrorCode, result["code"]))
        
        return success_response(result)
    except Exception as e:
        logger.error(f"生成新闻总结失败: {str(e)}")
        return error_response(f"生成新闻总结失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/news/bbc", response_model=None)
async def get_bbc_news(
    limit: int = Query(NEWS_SETTINGS["default_news_limit"], ge=1, le=NEWS_SETTINGS["max_news_limit"]),
    news_service: NewsService = Depends(get_news_service)
):
    """获取BBC科技新闻"""
    try:
        news_items = await news_service.get_bbc_news(limit=limit)
        news_items_dict = news_service.format_news_items(news_items)
            
        return success_response({
            "items": news_items_dict,
            "count": len(news_items_dict)
        })
    except Exception as e:
        logger.error(f"获取BBC新闻失败: {str(e)}")
        return error_response(f"获取新闻失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)