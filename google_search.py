from langchain_google_community import GoogleSearchAPIWrapper
from langchain.tools import Tool
from dotenv import load_dotenv
from utils.logger import setup_logger
import os

logger = setup_logger('google_search')
load_dotenv()

def create_google_search_tool():
    search = GoogleSearchAPIWrapper(
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        google_cse_id=os.getenv("GOOGLE_CSE_ID")
    )
    
    def search_with_logging(query):
        logger.info(f"开始 Google 搜索: {query}")
        result = search.run(query)
        logger.info("搜索结果:")
        logger.info("-" * 50)
        logger.info(result)
        logger.info("-" * 50)
        logger.info(f"搜索完成，结果长度: {len(result)} 字符")
        return result
    
    return Tool(
        name="Google Search",
        description="用于在 Google 上搜索最新信息的工具",
        func=search_with_logging
    )