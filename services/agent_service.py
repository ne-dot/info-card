from typing import List, Optional
from datetime import datetime
import time
import uuid  # 添加uuid模块导入
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
    # 在类的初始化方法中添加 agent_model_config_dao
    def __init__(self, wired_service: WireNewsService, bbc_service: BBCNewsService, chat_service: DeepSeekService, db):
        self.wired_service = wired_service
        self.bbc_service = bbc_service
        self.chat_service = chat_service
        self.agent_dao = AgentDAO(db)
        self.agent_invocation_dao = AgentInvocationDAO(db)
        self.rss_entry_dao = RSSEntryDAO(db)
        self.agent_prompt_dao = AgentPromptDAO(db)
        # 添加 agent_model_config_dao 实例
        from dao.agent_model_config_dao import AgentModelConfigDAO
        self.agent_model_config_dao = AgentModelConfigDAO(db)
        self.db = db
    
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

    async def get_all_agents(self, request):
        """获取所有Agent，支持分页
        
        Args:
            request: AgentListRequest 对象，包含分页参数和用户ID
        
        Returns:
            dict: 包含agents列表和分页信息的字典
        """
        try:
            # 获取所有Agent
            agents, total = self.agent_dao.get_all_agents(
                user_id=request.user_id,
                page=request.page, 
                page_size=request.page_size
            )
            
            # 转换为响应格式
            agent_list = []
            for agent in agents:
                agent_list.append({
                    'key_id': agent.key_id,
                    'name': agent.name,
                    'name_en': agent.name_en,
                    'name_zh': agent.name_zh,
                    'description': agent.description,
                    'pricing': agent.pricing,
                    'visibility': agent.visibility,
                    'status': agent.status,
                    'type': agent.type,
                    'create_date': agent.create_date,
                    'update_date': agent.update_date
                })
            
            # 返回结果
            return {
                'agents': agent_list,
                'total': total,
                'page': request.page,
                'page_size': request.page_size,
                'total_pages': (total + request.page_size - 1) // request.page_size
            }
        except Exception as e:
            logger.error(f"获取所有Agent服务失败: {str(e)}")
            raise Exception(f"获取所有Agent失败: {str(e)}")

    async def create_agent(self, agent_data, user_id):
        """创建一个新的Agent
        
        Args:
            agent_data: AgentCreateRequest 对象，包含创建Agent所需的参数
            user_id: 用户ID
        
        Returns:
            dict: 创建的Agent信息
        """
        try:
            # 调用DAO层创建Agent
            agent = self.agent_dao.create_agent(
                user_id=user_id,
                name=agent_data.name,
                name_en=agent_data.name_en,
                name_zh=agent_data.name_zh,
                description=agent_data.description,
                pricing=agent_data.pricing,
                visibility=agent_data.visibility,
                status=agent_data.status,
                type="assistant"  # 默认类型为assistant
            )
            
            # 构建返回结果
            result = {
                'key_id': agent.key_id,
                'name': agent.name,
                'name_en': agent.name_en,
                'name_zh': agent.name_zh,
                'description': agent.description,
                'pricing': agent.pricing,
                'visibility': agent.visibility,
                'status': agent.status,
                'type': agent.type,
                'create_date': agent.create_date
            }
            
            return result
        except Exception as e:
            logger.error(f"创建Agent服务失败: {str(e)}")
            raise Exception(f"创建Agent失败: {str(e)}")

    async def update_agent(self, agent_id: str, agent_data, user_id: str):
        """更新Agent信息
        
        Args:
            agent_id: Agent的ID
            agent_data: 更新的Agent数据
            user_id: 当前用户ID
            
        Returns:
            dict: 更新后的Agent信息
        """
        try:
            # 获取Agent
            agent = self.agent_dao.get_agent_by_key_id(agent_id)
            if not agent:
                raise Exception(f"找不到ID为{agent_id}的Agent")
            
            # 检查权限
            if agent.user_id != user_id:
                raise Exception("您没有权限修改此Agent")
            
            # 准备更新数据
            update_data = {
                "name": agent_data.name,
                "description": agent_data.description,
                "pricing": agent_data.pricing,
                "visibility": agent_data.visibility,
                "status": agent_data.status
            }
            
            # 如果提供了英文名和中文名，也更新它们
            if agent_data.name_en:
                update_data["name_en"] = agent_data.name_en
            if agent_data.name_zh:
                update_data["name_zh"] = agent_data.name_zh
            
            # 调用DAO层更新Agent
            updated_agent = self.agent_dao.update_agent(agent_id, **update_data)
            
            # 构建返回结果
            result = {
                'key_id': updated_agent.key_id,
                'name': updated_agent.name,
                'name_en': updated_agent.name_en,
                'name_zh': updated_agent.name_zh,
                'description': updated_agent.description,
                'pricing': updated_agent.pricing,
                'visibility': updated_agent.visibility,
                'status': updated_agent.status,
                'type': updated_agent.type,
                'update_date': updated_agent.update_date
            }
            
            return result
        except Exception as e:
            logger.error(f"更新Agent服务失败: {str(e)}")
            raise Exception(f"更新Agent失败: {str(e)}")

    async def config_agent(self, agent_id: str, config_data, user_id: str):
        """配置Agent的提示词、工具、模型等参数
        
        Args:
            agent_id: Agent的ID
            config_data: 配置数据，包含提示词、工具ID、模型ID和模型参数
            user_id: 当前用户ID
            
        Returns:
            dict: 配置结果
        """
        try:
            # 获取Agent
            agent = self.agent_dao.get_agent_by_key_id(agent_id)
            if not agent:
                raise Exception(f"找不到ID为{agent_id}的Agent")
            
            # 检查权限
            if agent.user_id != user_id:
                raise Exception("您没有权限配置此Agent")
            
            # 更新提示词 - 修改为使用agent_prompt_dao
            if config_data.prompt_zh or config_data.prompt_en:
                # 获取Agent现有的提示词
                prompts = self.agent_prompt_dao.get_prompts_by_agent_id(agent_id)
                
                if prompts and len(prompts) > 0:
                    # 如果已有提示词，更新第一个提示词
                    prompt_id = prompts[0].id
                    prompt_data = {}
                    
                    if config_data.prompt_zh:
                        prompt_data["content_zh"] = config_data.prompt_zh
                    if config_data.prompt_en:
                        prompt_data["content_en"] = config_data.prompt_en
                    
                    # 更新提示词
                    self.agent_prompt_dao.update_prompt(prompt_id, **prompt_data)
                    logger.info(f"已更新Agent {agent_id} 的提示词")
                else:
                    # 如果没有提示词，创建新的提示词
                    prompt_data = {
                        "agent_id": agent_id,
                        "creator_id": user_id,  # 修改这里，使用creator_id而不是user_id
                        "content_zh": config_data.prompt_zh if config_data.prompt_zh else None,
                        "content_en": config_data.prompt_en if config_data.prompt_en else None,
                        "version": "1.0.0",
                        "is_production": True
                    }
                    
                    # 创建提示词
                    self.agent_prompt_dao.create_prompt(**prompt_data)
                    logger.info(f"已为Agent {agent_id} 创建新的提示词")
            
            # 更新工具配置
            if config_data.tool_ids is not None:
                # 删除现有的所有工具关联
                self.agent_dao.remove_all_agent_tools(agent_id)
                logger.info(f"已删除Agent {agent_id} 的所有工具关联")
                
                # 添加新的工具关联
                if config_data.tool_ids and len(config_data.tool_ids) > 0:
                    for tool_id in config_data.tool_ids:
                        self.agent_dao.add_agent_tool(agent_id, tool_id)
                    logger.info(f"已为Agent {agent_id} 添加 {len(config_data.tool_ids)} 个工具关联")
            
            # 更新模型配置关联
            if hasattr(config_data, 'model_id') and config_data.model_id:
                # 更新Agent的model_config_id字段
                self.agent_dao.update_agent(agent_id, model_config_id=config_data.model_id)
                logger.info(f"已为Agent {agent_id} 设置模型配置 {config_data.model_id}")
            
            # 返回配置结果
            return {
                "agent_id": agent_id,
                "status": "success",
                "message": "Agent配置已更新"
            }
        except Exception as e:
            logger.error(f"配置Agent服务失败: {str(e)}")
            raise Exception(f"配置Agent失败: {str(e)}")

    async def trigger_agent(self, agent_id: str, user_id: str, lang: str, query: str = None):
        """触发指定的Agent，获取AI响应
        
        Args:
            agent_id: Agent的ID
            user_id: 当前用户ID
            lang: 语言代码
            query: 查询字符串，可选参数
            
        Returns:
            dict: 包含AI响应和工具调用结果
        """
        try:
            # 获取Agent
            agent = self.agent_dao.get_agent_by_key_id(agent_id)
            if not agent:
                raise Exception(f"找不到ID为{agent_id}的Agent")
            
            # 检查权限
            if not agent.check_user_access(user_id):
                raise Exception("您没有权限触发此Agent")
            
            # 检查必要配置
            # 1. 检查模型配置
            if not agent.model_config_id:
                raise Exception("Agent未配置模型，无法触发")
            
            # 2. 检查提示词配置
            prompts = self.agent_prompt_dao.get_prompts_by_agent_id(agent_id)
            if not prompts or len(prompts) == 0:
                raise Exception("Agent未配置提示词，无法触发")
            
            # 获取模型配置 - 使用 await 调用异步方法
            model_config = await self.agent_model_config_dao.get_model_config_by_id(agent.model_config_id)
            if not model_config:
                raise Exception(f"找不到ID为{agent.model_config_id}的模型配置")
            
            logger.info(f"获取到的模型配置: {model_config}")
            
            # 使用工厂模式初始化AI服务
            from services.model_factory import ModelFactory
            try:
                ai_service = ModelFactory.create_model_service(
                    model_config["model_name"],  # 使用字典访问方式
                    model_config["config"]  # 使用字典访问方式
                )
            except Exception as model_error:
                logger.error(f"初始化模型服务失败: {str(model_error)}")
                raise Exception(f"初始化模型服务失败: {str(model_error)}")
            

            
            # 直接从数据库获取工具关联，而不是使用agent.tools
            tool_services = {}
            tool_results = {}
            tools = self.agent_dao.get_tools_by_agent_id(agent_id)
            
            if tools and len(tools) > 0:
                # 使用工厂模式初始化和调用工具服务
                from services.tool_factory import ToolFactory
                # 传递数据库连接和查询参数
                tool_services, tool_results = await ToolFactory.create_and_invoke_tools(tools, query=query, db=self.db)
        
            
            # 获取提示词
            prompt = prompts[0]  # 使用第一个提示词
            prompt_content = prompt.content_en if lang == "en" else prompt.content_zh
            
            # 使用ToolFactory的build_tool_prompt方法构建完整提示词和人类消息
            from services.tool_factory import ToolFactory
            system_prompt, human_message = ToolFactory.build_tool_prompt(
                tool_results=tool_results,
                tool_services=tool_services,
                base_prompt=prompt_content,
                lang=lang
            )
            
            # 创建调用记录 - 正确处理返回的对象
            invocation = self.agent_invocation_dao.create_invocation(
                agent_id=agent_id,
                user_id=user_id,
                input_text="触发Agent请求"
            )
            
            # 从返回的对象中获取ID
            invocation_id = invocation.id if hasattr(invocation, 'id') else str(invocation)
            
            # 标记开始处理，并保存system_prompt到input_params
            input_params = {"prompt": system_prompt}
            self.agent_invocation_dao.start_invocation(invocation_id, input_params=input_params)
            
            logger.info(f"开始处理Agent {agent_id} 的请求,system_prompt,human_message: {system_prompt},{human_message}")
            # 使用消息列表方式调用AI服务
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_message)
            ]
            ai_response = ai_service.invoke(messages)
            
            # 从响应中提取内容
            if hasattr(ai_response, 'content'):
                ai_response = ai_response.content
            
            # 更新Agent的触发时间
            self.agent_dao.update_agent_trigger_date(agent_id)
            
            # 完成调用记录，标记为成功
            metrics = {"output_text": ai_response}
            self.agent_invocation_dao.complete_invocation(
                invocation_id,
                success=True,
                metrics=metrics
            )

            # 保存工具调用结果
            if tool_results and tool_services:
                await ToolFactory.save_tool_results(
                    tool_results=tool_results,
                    tool_services=tool_services,
                    invocation_id=invocation_id,
                    result=ai_response,
                    user_id=user_id
                )
                logger.info(f"已保存Agent {agent_id} 的工具调用结果")
            
            # 返回结果
            return {
                "agent_id": agent_id,
                "ai_response": ai_response,
                "tool_results": tool_results,
                "invocation_id": invocation_id
            }
        except Exception as e:
            logger.error(f"触发Agent失败: {str(e)}")
            
            # 记录失败的调用
            try:
                if 'invocation_id' in locals():
                    # 如果已经创建了调用记录，更新它为失败
                    self.agent_invocation_dao.complete_invocation(
                        invocation_id,
                        success=False,
                        error=str(e)
                    )
                else:
                    # 如果还没有创建调用记录，创建一个失败的记录
                    invocation = self.agent_invocation_dao.create_invocation(
                        agent_id=agent_id,
                        user_id=user_id,
                        input_text="触发Agent请求"
                    )
                    # 从返回的对象中获取ID
                    invocation_id = invocation.id if hasattr(invocation, 'id') else str(invocation)
                    self.agent_invocation_dao.complete_invocation(
                        invocation_id,
                        success=False,
                        error=str(e)
                    )
            except Exception as inner_e:
                logger.error(f"记录失败调用时出错: {str(inner_e)}")
            
            raise Exception(f"触发Agent失败: {str(e)}")