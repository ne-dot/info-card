from typing import List, Optional
from datetime import datetime
import time
from fastapi import Request
from sqlalchemy.orm import Session
from dao.agent_dao import AgentDAO
from dao.agent_invocation_dao import AgentInvocationDAO
from dao.rss_entry_dao import RSSEntryDAO
from dao.agent_prompt_dao import AgentPromptDAO
from services.deepseek_service import DeepSeekService
from services.wired_news_service import WireNewsService
from services.bbc_news_service import BBCNewsService
from models.news import NewsItem
from utils.logger import setup_logger
from utils.i18n_utils import get_text
from langchain.schema import HumanMessage, SystemMessage

logger = setup_logger('agent_service')

class AgentService:
    def __init__(self, wired_service: WireNewsService, bbc_service: BBCNewsService, chat_service: DeepSeekService, db):
        self.wired_service = wired_service
        self.bbc_service = bbc_service
        self.chat_service = chat_service
        self.agent_dao = AgentDAO(db)
        self.agent_invocation_dao = AgentInvocationDAO(db)
        self.rss_entry_dao = RSSEntryDAO(db)
        self.agent_prompt_dao = AgentPromptDAO(db)
    
    async def fetch_all_news(self, limit: int) -> tuple[List[NewsItem], List[str]]:
        """获取所有来源的新闻
        
        Returns:
            tuple[List[NewsItem], List[str]]: 新闻列表和feed_id列表
        """
        wired_news_items, wired_feed_id = await self.wired_service.get_wired_news(limit=limit)
        bbc_news_items, bbc_feed_id = await self.bbc_service.get_bbc_news(limit=limit)
        
        # 收集所有有效的feed_ids
        feed_ids = []
        if wired_feed_id:
            feed_ids.append(wired_feed_id)
        if bbc_feed_id:
            feed_ids.append(bbc_feed_id)
            
        return wired_news_items + bbc_news_items, feed_ids
    
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
    
    async def generate_tech_news_summary(self, request: Request = None, limit: int = 10, user_id: str = None) -> dict:
        """生成科技新闻总结
        
        Args:
            request: 请求对象，可选
            limit: 获取的新闻数量
            user_id: 用户ID，可选，如果提供则优先使用
        """
        try:
            # 1. 获取AI科技新闻agent
            tech_agents = self.agent_dao.get_agents_by_type("technews")
            if not tech_agents:
                logger.error("未找到技术新闻Agent")
                return {"error": "未找到技术新闻Agent", "code": "AGENT_NOT_FOUND"}
            
            tech_agent = tech_agents[0]
            logger.info(f"使用技术新闻Agent: {tech_agent.name}")
            
            # 2. 确定语言
            lang = 'en'
            if request and hasattr(request.state, 'lang'):
                lang = request.state.lang
            is_chinese = lang.startswith('zh')
            logger.info(f"使用{'中文' if is_chinese else '英文'}生成新闻总结")

            # 3. 创建触发记录 - 修改为使用agent_invocation_dao
            # 优先使用传入的user_id，其次从request中获取
            if user_id is None and request and hasattr(request.state, 'user'):
                user_id = request.state.user.user_id  # 修正这里，使用user_id而不是id
            
            invocation = self.agent_invocation_dao.create_invocation(
                agent_id=tech_agent.key_id,
                user_id=user_id,
                input_text="获取最新科技新闻",
            )
            invocation_id = invocation.id
            
            # 4. 更新AI科技新闻agent触发事件
            self.agent_dao.update_agent_trigger_date(tech_agent.key_id)
            
            # 5. 获取新闻数据
            all_news_items, feed_ids = await self.fetch_all_news(limit)
            if not all_news_items:
                self.agent_invocation_dao.complete_invocation(
                    invocation_id,
                    success=False,
                    error="未找到科技新闻"
                )
    
                return {"error": "未找到科技新闻", "code": "NOT_FOUND"}
            
            # 6. 将新闻数据转换为JSON格式，稍后一次性存储
            news_items_json = self.format_news_items(all_news_items)
            
            # 7. 获取Agent的提示词 - 从AgentPrompt获取
            prompts = self.agent_prompt_dao.get_prompts_by_agent_id(tech_agent.key_id)
            if not prompts:
                logger.error(f"未找到Agent {tech_agent.key_id} 的提示词")
                self.agent_invocation_dao.complete_invocation(
                    invocation_id,
                    success=False,
                    error="未找到Agent提示词"
                )
                return {"error": "未找到Agent提示词", "code": "PROMPT_NOT_FOUND"}
            
            # 选择提示词 - 由于不确定属性名，先使用第一个提示词
            prompt = prompts[0]
            
            # 尝试获取提示词内容，根据实际属性名调整
            prompt_template = None
            try:
                # 尝试不同的可能的属性名
                if hasattr(prompt, 'content_cn') and is_chinese:
                    prompt_template = prompt.content_cn
                elif hasattr(prompt, 'content_en') and not is_chinese:
                    prompt_template = prompt.content_en
                elif hasattr(prompt, 'content_zh') and is_chinese:
                    prompt_template = prompt.content_zh
                elif hasattr(prompt, 'content'):
                    prompt_template = prompt.content
                else:
                    # 如果找不到合适的属性，使用字符串表示
                    prompt_template = str(prompt)
            except Exception as attr_error:
                logger.error(f"获取提示词内容失败: {str(attr_error)}")
                prompt_template = "请总结以下科技新闻的要点。"  # 使用默认提示词
            
            # 组合完整提示词
            news_item_format = get_text("news.news_item_format", lang)
            news_text = self.build_news_text(all_news_items, news_item_format)
            full_prompt = f"{prompt_template}\n\n{'新闻内容:' if is_chinese else 'News content:'}\n{news_text}"
            
            # 8. AI请求
            logger.info(f"开始生成新闻总结: {full_prompt}")  # Remove the second parameter from logger.info
            # 标记开始处理，并保存full_prompt到input_params
            input_params = {"prompt": full_prompt}
            self.agent_invocation_dao.start_invocation(invocation_id, input_params=input_params)
            
            human_message = get_text("news.summary_prompt", lang)
            messages = [
                SystemMessage(content=full_prompt),
                HumanMessage(content=human_message)
            ]
            response = self.chat_service.invoke(messages)
            
            # 9. 处理AI响应
            if not response or not hasattr(response, 'content'):
                logger.error("新闻总结响应无效")
                self.agent_invocation_dao.complete_invocation(
                    invocation_id,
                    success=False,
                    error="AI响应无效"
                )
                return {"error": "生成新闻总结失败", "code": "AI_RESPONSE_ERROR"}
            
            summary = response.content
            logger.info("新闻总结生成成功")
            
            # 10. 更新调用记录为成功
            metrics = {"output_text": summary}
            self.agent_invocation_dao.complete_invocation(
                invocation_id,
                success=True,
                metrics=metrics
            )
            
            # 11. 存储新闻数据和总结
            try:
                self.rss_entry_dao.save_entry(
                    title="科技新闻总结",
                    description="自动生成的科技新闻总结",
                    link="",
                    published_date=datetime.now(),
                    source="agent",
                    categories=["tech", "news", "summary"],
                    feed_ids=feed_ids,  # 使用收集到的feed_ids
                    invocation_id=invocation_id,
                    raw_data=news_items_json,
                    summary=summary
                )
                logger.info("新闻数据和总结已存储")
            except Exception as save_error:
                logger.error(f"存储新闻数据和总结失败: {str(save_error)}")
                # 不影响主流程，继续返回结果
            
            return {
                "summary": summary,
                "news_count": len(all_news_items),
                "generated_at": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"生成新闻总结失败: {str(e)}")
            
            # 记录失败的触发
            try:
                if 'invocation_id' in locals():
                    # 如果已经创建了触发记录，更新它
                    self.agent_invocation_dao.complete_invocation(
                        invocation_id,
                        success=False,
                        error=str(e)
                    )
            except Exception as inner_e:
                logger.error(f"记录失败触发时出错: {str(inner_e)}")
            
            return {"error": f"生成新闻总结失败: {str(e)}", "code": "UNKNOWN_ERROR"}