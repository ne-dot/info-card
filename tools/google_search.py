from langchain_google_community import GoogleSearchAPIWrapper
from utils.logger import setup_logger
from config.settings import GOOGLE_API_KEY, GOOGLE_CSE_ID
import json
import requests

logger = setup_logger('google_search')

def create_google_search():
    return GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID
    )

async def search_google_by_text(query: str):
    try:
        logger.info(f"开始 Google 文本搜索: {query}")
        
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
        
        logger.info("文本搜索结果:")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    except Exception as e:
        logger.error(f"Google 文本搜索失败: {str(e)}")
        raise e

async def search_google_by_image(query: str):
    try:
        logger.info(f"开始 Google 图片搜索: {query}")
        
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "cx": GOOGLE_CSE_ID,
            "key": GOOGLE_API_KEY,
            "searchType": "image",
            "num": 5
        }

        response = requests.get(search_url, params=params)
        results = response.json()
        
        formatted_results = []
        if "items" in results:
            for item in results["items"]:
                formatted_result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'thumbnailLink': item.get('image', {}).get('thumbnailLink', ''),
                    'contextLink': item.get('contextLink', ''),
                    'source': 'google_image'
                }
                formatted_results.append(formatted_result)
        
        logger.info("图片搜索结果:")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    except Exception as e:
        logger.error(f"Google 图片搜索失败: {str(e)}")
        raise e