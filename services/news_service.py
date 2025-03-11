from typing import List, Optional
from datetime import datetime
import time
from fastapi import Request
from sqlalchemy.orm import Session
from services.wired_news_service import WireNewsService
from services.bbc_news_service import BBCNewsService
from services.deepseek_service import DeepSeekService
from models.news import NewsItem
from dao.news_dao import NewsDAO
from utils.logger import setup_logger
from utils.i18n_utils import get_text
from langchain.schema import HumanMessage, SystemMessage
from config.prompts.news_prompts import get_news_summary_prompt, get_news_summary_prompt_en

logger = setup_logger('news_service')

class NewsService:
    def __init__(self, wired_service: WireNewsService, bbc_service: BBCNewsService, chat_service: DeepSeekService, db):
        self.wired_service = wired_service
        self.bbc_service = bbc_service
        self.chat_service = chat_service
        self.news_dao = NewsDAO(db)
    
    async def get_wired_news(self, limit: int) -> List[NewsItem]:
        """获取Wired科技新闻"""
        return await self.wired_service.get_wired_news(limit=limit)
    
    async def get_bbc_news(self, limit: int) -> List[NewsItem]:
        """获取BBC科技新闻"""
        return await self.bbc_service.get_bbc_news(limit=limit)
    
    async def fetch_all_news(self, limit: int) -> List[NewsItem]:
        """获取所有来源的新闻"""
        wired_news_items = await self.wired_service.get_wired_news(limit=limit)
        bbc_news_items = await self.bbc_service.get_bbc_news(limit=limit)
        return wired_news_items + bbc_news_items
    
    def format_news_items(self, news_items: List[NewsItem]) -> List[dict]:
        """将新闻项转换为可序列化的字典"""
        news_items_dict = []
        for item in news_items:
            item_dict = item.dict()
            # 将datetime转换为ISO格式字符串
            item_dict['published_date'] = item.published_date.isoformat()
            news_items_dict.append(item_dict)
        return news_items_dict
    
    def build_news_text(self, news_items: List[NewsItem], news_item_format: str) -> str:
        """构建新闻文本"""
        news_text = ""
        for i, item in enumerate(news_items, 1):
            news_text += news_item_format.format(
                index=i,
                title=item.title,
                description=item.description,
                categories=', '.join(item.categories),
                source=item.source,
                published_date=item.published_date.strftime('%Y-%m-%d'),
                link=item.link
            )
        return news_text
    
    async def generate_news_summary(self, request: Request, db: Session, limit: int) -> dict:
        """生成新闻总结"""
        try:
            # 1. 获取新闻数据
            all_news_items = await self.fetch_all_news(limit)
            
            if not all_news_items:
                return {"error": "未找到科技新闻", "code": "NOT_FOUND"}
            
            # 2. 确定语言
            lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
            is_chinese = lang.startswith('zh')
            logger.info(f"使用{'中文' if is_chinese else '英文'}生成新闻总结")
            
            # 3. 保存新闻到数据库 - 使用NewsDAO
            db_news_items = self.news_dao.save_news_to_db(all_news_items)
            
            # 4. 构建新闻文本
            news_item_format = get_text("news.news_item_format", lang)
            news_text = self.build_news_text(all_news_items, news_item_format)
            
            # 5. 准备AI请求
            prompt_content = get_news_summary_prompt(news_text) if is_chinese else get_news_summary_prompt_en(news_text)
            human_message = get_text("news.summary_prompt", lang)
            messages = [
                SystemMessage(content=prompt_content),
                HumanMessage(content=human_message)
            ]
            
            # 在generate_news_summary方法中修改以下部分:
            
            # 6. 创建触发记录 - 使用NewsDAO
            user_id = request.state.user.user_id if hasattr(request.state, 'user') else None
            trigger_result = self.news_dao.create_trigger_record(user_id, request.client.host)
            trigger_id = trigger_result["id"]
            
            # 7. 调用AI生成摘要
            logger.info("开始生成新闻总结")
            response = self.chat_service.invoke(messages)
            
            # 8. 处理AI响应
            if response and hasattr(response, 'content'):
                summary = response.content
                logger.info("新闻总结生成成功")
                
                # 9. 保存摘要到数据库 - 使用NewsDAO
                news_item_ids = [item.id for item in db_news_items]
                self.news_dao.save_summary_to_db(summary, lang, trigger_id, news_item_ids)
                
                return {
                    "summary": summary,
                    "news_count": len(all_news_items),
                    "generated_at": datetime.now().isoformat()
                }
            else:
                logger.error("新闻总结响应无效")
                # 使用NewsDAO更新触发记录为失败
                self.news_dao.update_trigger_failure(trigger_id, "AI响应无效")  # 修改这里，使用trigger_id而不是trigger.id
                return {"error": "生成新闻总结失败", "code": "AI_RESPONSE_ERROR"}
                
        except Exception as e:
            logger.error(f"生成新闻总结失败: {str(e)}")
            
            # 记录失败的触发 - 使用NewsDAO
            user_id = request.state.user.user_id if hasattr(request.state, 'user') else None
            self.news_dao.save_failed_trigger(user_id, request.client.host, str(e))
            
            return {"error": f"生成新闻总结失败: {str(e)}", "code": "UNKNOWN_ERROR"}