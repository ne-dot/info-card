from langchain_google_community import GoogleSearchAPIWrapper
from langchain.tools import Tool
from dotenv import load_dotenv
from utils.logger import setup_logger
import os
import json

logger = setup_logger('google_search')
load_dotenv()

def create_google_search_tool():
    search = GoogleSearchAPIWrapper(
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        google_cse_id=os.getenv("GOOGLE_CSE_ID")
    )
    
    def search_with_logging(query):
        logger.info(f"开始 Google 搜索: {query}")
        
        # 获取原始搜索结果
        raw_results = search.results(query, num_results=5)
        
        # 格式化搜索结果
        formatted_results = []
        for result in raw_results:
            formatted_result = {
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('link', ''),
                'source': result.get('source', '')
            }
            formatted_results.append(formatted_result)
        
        # 记录日志
        logger.info("搜索结果:")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    
    return Tool(
        name="Google Search",
        description="用于在 Google 上搜索最新信息的工具",
        func=search_with_logging
    )