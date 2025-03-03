from langchain.schema import HumanMessage, SystemMessage
from config.prompts.search_prompts import searcher_system_prompt_cn, summary_prompt_cn
from utils.logger import setup_logger
from models.search_result import SearchResult
from services.deepseek_service import DeepSeekService
from tools.google_search import search_google_by_text, search_google_by_image
import json

logger = setup_logger('chat_service')

from langchain.tools import StructuredTool

class ChatService:
    def __init__(self, db):
        self.chat = DeepSeekService()
        self.db = db
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

    async def search_and_respond(self, query: str):
        logger.info(f"接收到查询请求: {query}")
        
        # 设置工具列表
        tools = [self.text_search_tool, self.image_search_tool]
        
        # 创建消息列表
        system_prompt = searcher_system_prompt_cn.format(
            tool_info="可以使用以下工具：\n1. text_search: 搜索文本信息\n2. image_search: 搜索图片信息"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"当前问题：{query}。你必须先使用text_search和image_search工具搜索相关信息，然后再提供回答。")
        ]
        
        # 调用大模型，启用工具调用
        logger.info(f"开始调用大模型，查询: {query}")
        try:
            gpt_response = self.chat.invoke(messages, tools=tools)
            logger.info(f"大模型响应类型: {type(gpt_response)}")
            if gpt_response:
                logger.info(f"大模型响应内容: {gpt_response}")
                
                # 检查是否有tool_calls属性
                if hasattr(gpt_response, 'tool_calls'):
                    logger.info(f"工具调用属性: {gpt_response.tool_calls}")
                else:
                    logger.info("响应中没有tool_calls属性")
                    
                # 检查其他可能的属性
                for attr in dir(gpt_response):
                    if not attr.startswith('_'):
                        try:
                            logger.info(f"响应属性 {attr}: {getattr(gpt_response, attr, None)}")
                        except Exception as e:
                            logger.info(f"无法获取属性 {attr}: {str(e)}")
            else:
                logger.error("大模型返回了空响应")
        except Exception as e:
            logger.error(f"调用大模型时出错: {str(e)}")
            gpt_response = None
        logger.info("大模型调用完成")
        
        # 处理工具调用结果
        final_results = []
        text_results = []
        image_results = []
        
        # 手动执行搜索，确保即使工具调用失败也能获取结果
        try:
            logger.info(f"执行文本搜索: {query}")
            text_results = json.loads(await self._text_search_wrapper(query))
            logger.info(f"文本搜索完成，获取到 {len(text_results)} 条结果")
            
            logger.info(f"执行图片搜索: {query}")
            image_results = json.loads(await self._image_search_wrapper(query))
            logger.info(f"图片搜索完成，获取到 {len(image_results)} 条结果")
        except Exception as e:
            logger.error(f"手动执行搜索失败: {str(e)}")
        
        # 如果有搜索结果，生成总结
        logger.info(f"文本结果数量: {len(text_results)}, 图片结果数量: {len(image_results)}")
        if text_results or image_results:
            logger.info("准备基于搜索结果生成总结")
            search_summary = ""
            if text_results:
                search_summary += "文本搜索结果:\n" + "\n".join([
                    f"- {result['title']}\n  摘要: {result['snippet']}\n  来源: {result['link']}"
                    for result in text_results
                ]) + "\n\n"
            
            if image_results:
                search_summary += "图片搜索结果:\n" + "\n".join([
                    f"- {result['title']}\n  摘要: {result.get('snippet', '')}\n  图片链接: {result['thumbnailLink']}\n  来源: {result['contextLink']}"
                    for result in image_results
                ])
            
            # 再次调用模型生成总结
            logger.info("调用大模型生成最终总结")
            summary_messages = [
                SystemMessage(content=summary_prompt_cn),
                HumanMessage(content=f"搜索结果：\n{search_summary}\n\n请针对问题「{query}」提供一个全面的总结。")
            ]
            
            try:
                summary_response = self.chat.invoke(summary_messages)
                if summary_response and hasattr(summary_response, 'content'):
                    final_results.append(SearchResult.from_gpt_response(summary_response.content))
                else:
                    logger.error("总结响应无效或缺少content属性")
                    final_results.append(SearchResult.from_gpt_response("无法生成总结，请稍后再试。"))
            except Exception as e:
                logger.error(f"生成总结失败: {str(e)}")
                final_results.append(SearchResult.from_gpt_response("生成总结时发生错误，请稍后再试。"))
        else:
            # 如果没有搜索结果，返回默认响应
            final_results.append(SearchResult.from_gpt_response("未找到相关信息，请尝试其他搜索词。"))
        
        # 添加搜索结果
        for result in text_results:
            final_results.append(SearchResult.from_google_result(result))
        
        for result in image_results:
            final_results.append(SearchResult.from_google_result(result))

        # 保存结果到数据库
        try:
            self.db.save_search_results(query, final_results)
            logger.info("搜索结果已保存到数据库")
        except Exception as e:
            logger.error(f"保存到数据库失败: {str(e)}")
        
        return final_results
