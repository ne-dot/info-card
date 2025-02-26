from langchain.schema import HumanMessage, SystemMessage
from deepseek_llm import DeepSeekChat
from config.prompts.search_prompts import searcher_system_prompt_cn
from utils.logger import setup_logger
from models.search_result import SearchResult
from config.settings import DEEPSEEK_API_KEY
from services.google_search import search_google
import json

logger = setup_logger('chat_service')

class ChatService:
    def __init__(self, db):
        self.chat = DeepSeekChat(api_key=DEEPSEEK_API_KEY)
        self.db = db

    async def search_and_respond(self, query: str):
        logger.info(f"接收到查询请求: {query}")
        
        # 执行 Google 搜索
        search_results = await search_google(query)
        
        # 将搜索结果转换为文本摘要
        search_summary = "\n".join([
            f"- {result['title']}\n  摘要: {result['snippet']}\n  来源: {result['link']}"
            for result in search_results
        ])
        
        # 创建消息列表
        system_prompt = searcher_system_prompt_cn.format(tool_info="Google Search: 用于在 Google 上搜索最新信息的工具")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"搜索结果：{search_summary}\n\n当前问题：{query}")
        ]
        
        # 获取 GPT 响应
        gpt_response = self.chat.invoke(messages)
        
        # 构建最终返回结果
        final_results = []
        
        # 添加 GPT 响应结果
        final_results.append(SearchResult.from_gpt_response(gpt_response.content))
        
        # 添加 Google 搜索结果
        for result in search_results:
            final_results.append(SearchResult.from_google_result(result))

         # 保存结果到数据库
        try:
            self.db.save_search_results(query, final_results)
            logger.info("搜索结果已保存到数据库")
        except Exception as e:
            logger.error(f"保存到数据库失败: {str(e)}")
        
        return final_results
