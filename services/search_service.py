from langchain.schema import HumanMessage, SystemMessage
from config.prompts.search_prompts import SEARCH_PROMPT_ZH, SEARCH_PROMPT_EN
from utils.logger import setup_logger
from models.search_result import SearchResult
from services.deepseek_service import DeepSeekService
from tools.google_search import search_google_by_text, search_google_by_image
from dao.agent_dao import AgentDAO
from dao.agent_invocation_dao import AgentInvocationDAO
from dao.ai_summary_dao import AISummaryDAO
from dao.search_raw_dao import SearchRawDAO
from utils.i18n_utils import get_text
import json

logger = setup_logger('search_service')

from langchain.tools import StructuredTool

class SearchService:
    def __init__(self, db):
        self.chat = DeepSeekService()
        self.agent_dao = AgentDAO(db)
        self.invocation_dao = AgentInvocationDAO(db)
        self.summary_dao = AISummaryDAO(db)
        self.search_raw_dao = SearchRawDAO(db)
        
        # 定义搜索工具
        self.text_search_tool = StructuredTool.from_function(
            func=self._text_search_wrapper,
            name="text_search",
            description="搜索与查询相关的文本信息。输入参数为查询字符串。",
            args_schema={"query": str},  # 明确定义参数
            return_direct=False
        )
        self.image_search_tool = StructuredTool.from_function(
            func=self._image_search_wrapper,
            name="image_search",
            description="搜索与查询相关的图片信息。输入参数为查询字符串。",
            args_schema={"query": str},  # 明确定义参数
            return_direct=False
        )

    async def _text_search_wrapper(self, query: str) -> str:
        try:
            results = await search_google_by_text(query)
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            logger.error(f"文本搜索工具调用失败: {str(e)}")
            return "[]"

    async def _image_search_wrapper(self, query: str) -> str:
        try:
            results = await search_google_by_image(query)
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            logger.error(f"图片搜索工具调用失败: {str(e)}")
            return "[]"

    async def search_and_respond(self, query: str, lang: str = 'en',  user_id: str = None, anonymous_id: str = None):
        logger.info(f"接收到查询请求: {query}, 语言: {lang}")
        
        # 获取搜索Agent
        search_agents = self.agent_dao.get_agents_by_type("search")
        
        if not search_agents:
            logger.warning("未找到搜索Agent，使用默认配置")
            agent_id = "default_search_agent"
        else:
            search_agent = search_agents[0]
            agent_id = search_agent.key_id
            
            # 检查用户是否有权限访问该Agent
            # 对于search类型的Agent，不需要检查订阅状态，因为search_agent.check_user_access总是返回True
            # 但我们仍然可以记录这个信息
            has_access = search_agent.check_user_access(user_id)
            requires_subscription = search_agent.requires_subscription()
            
            logger.info(f"Agent访问检查: agent_id={agent_id}, requires_subscription={requires_subscription}, has_access={has_access}")
            
            # 由于search类型的Agent不需要订阅，这里不需要额外的权限检查
            # 如果将来有其他类型的Agent，可以在这里添加权限检查逻辑
        
        # 1. 创建调用记录
        params = {
            "lang": lang,
            "anonymous_id": anonymous_id
        }
        invocation = self.invocation_dao.create_invocation(
            user_id=user_id or anonymous_id,
            agent_id=agent_id,
            input_text=query,
            input_params=params
        )
        
        # 2. 设置开始时间
        self.invocation_dao.start_invocation(invocation.id)
        
        # 初始化结果变量
        text_results = []
        image_results = []
        final_results = []
        summary_response = None
        
        try:
            # 3. 执行搜索
            logger.info(f"开始执行搜索: {query}")
            text_results = json.loads(await self._text_search_wrapper(query))
            image_results = json.loads(await self._image_search_wrapper(query))
            logger.info(f"搜索完成，文本结果: {len(text_results)}条，图片结果: {len(image_results)}条")
            
            # 4. 保存文本搜索结果
            if text_results:
                # 构建更详细的结构化数据
                text_structured_data = {
                    "total_results": len(text_results),
                    "result_items": text_results  # 保存完整的结果项
                }
                
                self.search_raw_dao.create_search_data(
                    invocation_id=invocation.id,
                    engine_type="google",
                    content_type="text",
                    request_data={"query": query},
                    response_data=text_results,
                    structured_data=text_structured_data
                )
            
            # 5. 保存图片搜索结果
            if image_results:
                # 构建更详细的结构化数据
                image_structured_data = {
                    "total_results": len(image_results),
                     "result_items": image_results  # 保存完整的结果项
                }
                
                self.search_raw_dao.create_search_data(
                    invocation_id=invocation.id,
                    engine_type="google",
                    content_type="image",
                    request_data={"query": query},
                    response_data=image_results,
                    structured_data=image_structured_data
                )
            
            # 准备搜索结果摘要
            search_summary = self._prepare_search_summary(text_results, lang)
            
            # 构建人类消息
            human_message = self._build_human_message(query, search_summary, lang)
            
            # 获取系统提示词
            system_prompt = self._get_system_prompt(search_agents, lang)
            
            # 创建消息列表
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_message)
            ]
            
            # 6. 调用大模型生成总结
            logger.info(f"开始生成总结")
            summary_content = self._generate_summary(messages, lang)
            
            if summary_content:
                final_results.append(SearchResult.from_gpt_response(summary_content))
                
                # 7. 保存AI总结
                summary_metadata = {
                    'model': 'deepseek',
                    'query': query,
                    'language': lang,
                    'text_sources_count': len(text_results),
                    'image_sources_count': len(image_results)
                }
                
                self.summary_dao.create_summary(
                    invocation_id=invocation.id,
                    content=summary_content,
                    metadata=summary_metadata
                )

             # 8. 完成调用记录
            metrics = {
                'text_results_count': len(text_results),
                'image_results_count': len(image_results),
                'response_length': len(summary_content) if summary_content else 0
            }
            
            self.invocation_dao.complete_invocation(
                invocation_id=invocation.id,
                success=True,
                metrics=metrics
            )
            
            # 如果如果没有搜索结果且总结生成失败，返回默认响应
            if not final_results:
                no_results_msg = get_text("no_search_results", lang)
                final_results.append(SearchResult.from_gpt_response(no_results_msg))
            
            # 添加图片搜索结果
            for result in image_results:
                final_results.append(SearchResult.from_google_result(result))

        except Exception as e:
            # 记录错误并完成调用
            error_msg = f"处理查询失败: {str(e)}"
            logger.error(error_msg)
            
            self.invocation_dao.complete_invocation(
                invocation_id=invocation.id,
                success=False,
                error=error_msg
            )
            
            # 返回错误信息
            error_response = get_text("search_error", lang)
            return [SearchResult.from_gpt_response(error_response)]
        
        return final_results
    
    # 添加辅助方法，将复杂逻辑拆分出来
    def _prepare_search_summary(self, text_results, lang):
        """准备搜索结果摘要"""
        search_summary = ""
        
        if lang.startswith('en'):
            # 英文版本
            if text_results:
                search_summary += "Text search results:\n" + "\n".join([
                    f"- Title: {result['title']}\n  Summary: {result['snippet']}\n  Source: [{result.get('displayLink', 'Unknown Source')}]({result['link']})"
                    for result in text_results
                ]) + "\n\n"
            else:
                search_summary += "No text search results found.\n\n"
        else:
            # 中文版本
            if text_results:
                search_summary += "文本搜索结果:\n" + "\n".join([
                    f"- 标题: {result['title']}\n  摘要: {result['snippet']}\n  来源: [{result.get('displayLink', '未知来源')}]({result['link']})"
                    for result in text_results
                ]) + "\n\n"
            else:
                search_summary += "未找到文本搜索结果。\n\n"
        
        return search_summary
    
    def _build_human_message(self, query, search_summary, lang):
        """构建人类消息"""
        if lang.startswith('en'):
            return f"Question: \"{query}\"\n\nSearch results:\n{search_summary}\n\nPlease analyze these search results and provide a comprehensive summary according to the instructions."
        else:
            return f"问题：「{query}」\n\n搜索结果：\n{search_summary}\n\n请根据指示分析这些搜索结果并提供全面的总结。"
    
    def _get_system_prompt(self, search_agents, lang):
        """获取系统提示词"""
        try:
            if search_agents:
                search_agent = search_agents[0]
                logger.info(f"使用搜索Agent: {search_agent.name}, key_id: {search_agent.key_id}")
                
                agent_prompt = self.agent_dao.get_agent_prompt(search_agent.key_id)
                
                if agent_prompt:
                    system_prompt = agent_prompt.content_en if lang.startswith('en') else agent_prompt.content_zh
                    self.agent_dao.update_agent_trigger_date(search_agent.key_id)
                    return system_prompt
            
            # 如果没有找到Agent或提示词，使用默认提示词
            logger.warning("使用默认提示词")
            return SEARCH_PROMPT_EN if lang.startswith('en') else SEARCH_PROMPT_ZH
        
        except Exception as e:
            logger.error(f"获取搜索Agent提示词失败: {str(e)}")
            return SEARCH_PROMPT_EN if lang.startswith('en') else SEARCH_PROMPT_ZH
    
    def _generate_summary(self, messages, lang):
        """生成总结内容"""
        try:
            summary_response = self.chat.invoke(messages)
            if summary_response and hasattr(summary_response, 'content'):
                logger.info("总结生成成功")
                return summary_response.content
            else:
                logger.error("总结响应无效")
                return get_text("summary_generation_failed", lang)
        except Exception as e:
            logger.error(f"生成总结失败: {str(e)}")
            return get_text("summary_error", lang)
