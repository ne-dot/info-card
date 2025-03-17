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
from dao.agent_dao import AgentDAO
from utils.logger import setup_logger
from utils.i18n_utils import get_text
from langchain.schema import HumanMessage, SystemMessage
from config.prompts.news_prompts import get_news_summary_prompt, get_news_SEARCH_PROMPT_EN

logger = setup_logger('news_service')

class NewsService:
    def __init__(self, wired_service: WireNewsService, bbc_service: BBCNewsService, chat_service: DeepSeekService, db):
        self.wired_service = wired_service
        self.bbc_service = bbc_service
        self.chat_service = chat_service
        self.news_dao = NewsDAO(db)
        self.agent_dao = AgentDAO(db)  # 添加AgentDAO实例
    
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
            # 1. 获取AI科技新闻agent
            tech_agents = self.agent_dao.get_agents_by_type("technews")
            if not tech_agents:
                logger.error("未找到技术新闻Agent")
                return {"error": "未找到技术新闻Agent", "code": "AGENT_NOT_FOUND"}
            
            tech_agent = tech_agents[0]
            logger.info(f"使用技术新闻Agent: {tech_agent.name}")
            
            # 2. 确定语言
            lang = request.state.lang if hasattr(request.state, 'lang') else 'en'
            is_chinese = lang.startswith('zh')
            logger.info(f"使用{'中文' if is_chinese else '英文'}生成新闻总结")

            # 3. 创建触发记录 - 修改获取key_id
            user_id = request.state.user.user_id if hasattr(request.state, 'user') else None
            trigger_result = self.news_dao.create_trigger_record(
                user_id=user_id, 
                ip_address=request.client.host,
                agent_id=tech_agent.key_id
            )
            trigger_key_id = trigger_result.get("key_id")  # 确保获取的是key_id而不是id
            
            # 4. 更新AI科技新闻agent触发事件
            self.agent_dao.update_agent_trigger_date(tech_agent.key_id)
            
            # 5. 获取新闻数据
            all_news_items = await self.fetch_all_news(limit)
            if not all_news_items:
                self.news_dao.update_trigger_failure(trigger_key_id, "未找到科技新闻")
                return {"error": "未找到科技新闻", "code": "NOT_FOUND"}
            
            # 6. 保存所有新闻 - 提前保存新闻数据
            self.news_dao.save_news_to_db(all_news_items, trigger_key_id)
            
            # 7. 组合完整提示词
            news_item_format = get_text("news.news_item_format", lang)
            news_text = self.build_news_text(all_news_items, news_item_format)
            
            # 选择对应语言的提示词
            prompt_template = tech_agent.prompt_zh if is_chinese else tech_agent.prompt_en
            full_prompt = f"{prompt_template}\n\n{'新闻内容:' if is_chinese else 'News content:'}\n{news_text}"
            
            # 8. AI请求
            logger.info("开始生成新闻总结")
            human_message = get_text("news.summary_prompt", lang)
            messages = [
                SystemMessage(content=full_prompt),
                HumanMessage(content=human_message)
            ]
            response = self.chat_service.invoke(messages)
            
            # 9. 处理AI响应
            if not response or not hasattr(response, 'content'):
                logger.error("新闻总结响应无效")
                self.news_dao.update_trigger_failure(trigger_key_id, "AI响应无效")
                return {"error": "生成新闻总结失败", "code": "AI_RESPONSE_ERROR"}
            
            summary = response.content
            logger.info("新闻总结生成成功")
            
            # 10. 保存AI总结
            self.news_dao.save_summary_to_db(summary, lang, trigger_key_id)
            
            return {
                "summary": summary,
                "news_count": len(all_news_items),
                "generated_at": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"生成新闻总结失败: {str(e)}")
            
            # 记录失败的触发 - 使用一致的方法
            try:
                user_id = request.state.user.user_id if hasattr(request.state, 'user') else None
                if 'trigger_key_id' in locals():
                    # 如果已经创建了触发记录，更新它
                    self.news_dao.update_trigger_failure(trigger_key_id, str(e))
                else:
                    # 否则创建一个新的失败记录
                    self.news_dao.create_failed_trigger(user_id, request.client.host, str(e))
            except Exception as inner_e:
                logger.error(f"记录失败触发时出错: {str(inner_e)}")
            
            return {"error": f"生成新闻总结失败: {str(e)}", "code": "UNKNOWN_ERROR"}