from langchain.schema import HumanMessage, SystemMessage
from config.prompts.search_prompts import searcher_system_prompt_cn, summary_prompt_cn, searcher_system_prompt_en, summary_prompt_en
from utils.logger import setup_logger
from models.search_result import SearchResult
from services.deepseek_service import DeepSeekService
from tools.google_search import search_google_by_text, search_google_by_image
from dao.search_dao import SearchDAO
from utils.i18n_utils import get_text
import json

logger = setup_logger('chat_service')

from langchain.tools import StructuredTool

class ChatService:
    def __init__(self, db):
        self.chat = DeepSeekService()
        self.search_dao = SearchDAO(db)
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

    async def search_and_respond(self, query: str, lang: str = 'en'):
        logger.info(f"接收到查询请求: {query}, 语言: {lang}")
        
        # 手动执行搜索，获取结果
        try:
            # 减少日志，只记录开始搜索
            logger.info(f"开始执行搜索: {query}")
            text_results = json.loads(await self._text_search_wrapper(query))
            image_results = json.loads(await self._image_search_wrapper(query))
            # 只记录搜索结果数量
            logger.info(f"搜索完成，文本结果: {len(text_results)}条，图片结果: {len(image_results)}条")
        except Exception as e:
            logger.error(f"执行搜索失败: {str(e)}")
            text_results = []
            image_results = []
        
        # 准备搜索结果摘要
        search_summary = ""
        
        # 根据语言选择不同的提示词和搜索结果格式
        if lang.startswith('en'):
            # 英文版本
            if text_results:
                search_summary += "Text search results:\n" + "\n".join([
                    f"- {result['title']}\n  Summary: {result['snippet']}\n  Source: {result['link']}"
                    for result in text_results
                ]) + "\n\n"
            
            system_prompt = summary_prompt_en
            human_message = f"Search results:\n{search_summary}\n\nPlease provide a comprehensive summary for the question \"{query}\"."
        else:
            # 中文版本
            if text_results:
                search_summary += "文本搜索结果:\n" + "\n".join([
                    f"- {result['title']}\n  摘要: {result['snippet']}\n  来源: {result['link']}"
                    for result in text_results
                ]) + "\n\n"
            
            system_prompt = summary_prompt_cn
            human_message = f"搜索结果：\n{search_summary}\n\n请针对问题「{query}」提供一个全面的总结。"
        
        # 创建消息列表，直接包含搜索结果
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ]
        
        # 调用大模型生成总结
        logger.info(f"开始生成总结")
        final_results = []
        
        try:
            summary_response = self.chat.invoke(messages)
            if summary_response and hasattr(summary_response, 'content'):
                # 简化日志
                logger.info("总结生成成功")
                final_results.append(SearchResult.from_gpt_response(summary_response.content))
            else:
                logger.error("总结响应无效")
                # 使用多语言工具获取错误消息
                error_msg = get_text("summary_generation_failed", lang)
                final_results.append(SearchResult.from_gpt_response(error_msg))
        except Exception as e:
            logger.error(f"生成总结失败: {str(e)}")
            # 使用多语言工具获取错误消息
            error_msg = get_text("summary_error", lang)
            final_results.append(SearchResult.from_gpt_response(error_msg))
        
        # 如果没有搜索结果且总结生成失败，返回默认响应
        if not final_results:
            # 使用多语言工具获取错误消息
            no_results_msg = get_text("no_search_results", lang)
            final_results.append(SearchResult.from_gpt_response(no_results_msg))
        
        # 添加图片搜索结果
        for result in image_results:
            final_results.append(SearchResult.from_google_result(result))
    
        # 保存结果到数据库
        try:
            await self.search_dao.save_search_results(query, final_results)
            # 简化日志
            logger.info("结果已保存到数据库")
        except Exception as e:
            logger.error(f"保存到数据库失败: {str(e)}")
        
        return final_results
