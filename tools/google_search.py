from langchain_google_community import GoogleSearchAPIWrapper
from utils.logger import setup_logger
from config.settings import GOOGLE_API_KEY, GOOGLE_CSE_ID
import json

logger = setup_logger('google_search')

def create_google_search():
    search = GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID
    )
    return search

async def search_google(query: str):
    try:
        logger.info(f"开始 Google 搜索: {query}")
        
        search = create_google_search()
        raw_results = search.results(query, num_results=5)
        
        formatted_results = []
        for result in raw_results:
            formatted_result = {
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('link', ''),
                'source': 'google'
            }
            formatted_results.append(formatted_result)
        
        logger.info("搜索结果:")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    except Exception as e:
        logger.error(f"Google 搜索失败: {str(e)}")
        raise e