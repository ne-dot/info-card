from fastapi import APIRouter, Depends, Request, Query
from typing import List, Optional
from datetime import datetime
from services.wired_news_service import WireNewsService
from services.bbc_news_service import BBCNewsService
from models.news import NewsItem, NewsResponse
from utils.response_utils import success_response, error_response, ErrorCode
from utils.logger import setup_logger
from config.prompts.news_prompts import get_news_summary_prompt, get_news_summary_prompt_en
from services.deepseek_service import DeepSeekService
from langchain.schema import HumanMessage, SystemMessage
from utils.i18n_utils import get_text

logger = setup_logger('news_controller')
router = APIRouter(tags=["新闻"], include_in_schema=True)

# 依赖项函数，用于创建服务实例 - 将所有依赖项函数放在一起
def get_news_service():
    return WireNewsService()

def get_bbc_news_service():
    return BBCNewsService()

def get_chat_service():
    return DeepSeekService()

# 然后是路由定义
@router.get("/news/wired", response_model=None)
async def get_wired_news(
    limit: int = Query(10, ge=1, le=50),
    news_service: WireNewsService = Depends(get_news_service)
):
    """获取Wired科技新闻"""
    try:
        news_items = await news_service.get_wired_news(limit=limit)
        
        # 将新闻项转换为可序列化的字典
        news_items_dict = []
        for item in news_items:
            item_dict = item.dict()
            # 将datetime转换为ISO格式字符串
            item_dict['published_date'] = item.published_date.isoformat()
            news_items_dict.append(item_dict)
            
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
    news_service: WireNewsService = Depends(get_news_service),
    bbc_news_service: BBCNewsService = Depends(get_bbc_news_service),
    chat_service: DeepSeekService = Depends(get_chat_service)
):
    """获取近期科技新闻总结"""
    try:
        # 使用固定的新闻数量
        limit = 10
        
        # 获取最新的科技新闻 (Wired和BBC)
        wired_news_items = await news_service.get_wired_news(limit=limit)
        bbc_news_items = await bbc_news_service.get_bbc_news(limit=limit)
        
        # 合并新闻列表
        all_news_items = wired_news_items + bbc_news_items
        
        if not all_news_items:
            return error_response("未找到科技新闻", ErrorCode.NOT_FOUND)
        
        # 使用request.state.lang判断语言
        lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
        is_chinese = lang.startswith('zh')
        
        # 记录使用的语言
        logger.info(f"使用{'中文' if is_chinese else '英文'}生成新闻总结")
        
        # 使用国际化模板构建新闻摘要文本
        news_text = ""
        news_item_format = get_text("news.news_item_format", lang)
        
        for i, item in enumerate(all_news_items, 1):
            news_text += news_item_format.format(
                index=i,
                title=item.title,
                description=item.description,
                categories=', '.join(item.categories),
                source=item.source,
                published_date=item.published_date.strftime('%Y-%m-%d'),
                link=item.link
            )
        
        # 从utils中获取prompt内容
        if is_chinese:
            prompt_content = get_news_summary_prompt(news_text)
            human_message = get_text("news.summary_prompt", lang)
        else:
            prompt_content = get_news_summary_prompt_en(news_text)
            human_message = get_text("news.summary_prompt", lang)
        
        # 创建消息列表，与search_service相同的方式
        messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content=human_message)
        ]
        
        # 使用DeepSeekService调用大模型
        logger.info("开始生成新闻总结")
        response = chat_service.invoke(messages)
        
        # 提取生成的内容
        if response and hasattr(response, 'content'):
            summary = response.content
            logger.info("新闻总结生成成功")
        else:
            logger.error("新闻总结响应无效")
            return error_response("生成新闻总结失败", ErrorCode.AI_RESPONSE_ERROR)
        
        return success_response({
            "summary": summary,
            "news_count": len(all_news_items),
            "generated_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"生成新闻总结失败: {str(e)}")
        return error_response(f"生成新闻总结失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/news/bbc", response_model=None)
async def get_bbc_news(
    request: Request,
    news_service: BBCNewsService = Depends(get_bbc_news_service)
):
    """获取BBC科技新闻"""
    try:
        # 使用固定的新闻数量
        limit = 10
        
        news_items = await news_service.get_bbc_news(limit=limit)
        
        # 将新闻项转换为可序列化的字典
        news_items_dict = []
        for item in news_items:
            item_dict = item.dict()
            # 将datetime转换为ISO格式字符串
            item_dict['published_date'] = item.published_date.isoformat()
            news_items_dict.append(item_dict)
            
        return success_response({
            "items": news_items_dict,
            "count": len(news_items_dict)
        })
    except Exception as e:
        logger.error(f"获取BBC新闻失败: {str(e)}")
        return error_response(f"获取新闻失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)