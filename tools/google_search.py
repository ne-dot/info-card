from langchain_google_community import GoogleSearchAPIWrapper
from utils.logger import setup_logger
from config.settings import GOOGLE_API_KEY, GOOGLE_CSE_ID
import json
import requests
from functools import lru_cache

logger = setup_logger('google_search')

@lru_cache(maxsize=1)
def get_google_search():
    return GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID
    )

async def search_google_by_text(query: str):
    try:
        logger.info(f"开始 Google 文本搜索: {query}")
        
        search = get_google_search()
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
        
        # 使用同一个搜索实例进行图片搜索和上下文搜索
        search = get_google_search()
        
        # 批量获取图片搜索结果
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "cx": GOOGLE_CSE_ID,
            "key": GOOGLE_API_KEY,
            "searchType": "image",
            "num": 5,
            "fields": "items(title,link,image/thumbnailLink,image/contextLink)"  # 只获取需要的字段
        }

        response = requests.get(search_url, params=params)
        results = response.json()
        
        formatted_results = []
        if "items" in results:
            # 收集所有需要搜索上下文的 URL
            context_urls = [item.get('image', {}).get('contextLink') 
                          for item in results['items'] 
                          if item.get('image', {}).get('contextLink')]
            
            # 批量获取上下文内容
            context_contents = {}
            if context_urls:
                for context_url in context_urls:
                    try:
                        # 对每个 URL 单独搜索，确保能获取到内容
                        context_results = search.results(f"site:{context_url}", num_results=1)
                        if context_results:
                            context_contents[context_url] = context_results[0].get('snippet', '')
                    except Exception as e:
                        logger.error(f"获取上下文内容失败 {context_url}: {str(e)}")
                        context_contents[context_url] = ''
            
            # 组装最终结果
            for item in results['items']:
                context_link = item.get('image', {}).get('contextLink', '')
                formatted_result = {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'thumbnailLink': item.get('image', {}).get('thumbnailLink', ''),
                    'contextLink': context_link,
                    'snippet': context_contents.get(context_link, ''),  # 改用 snippet 替代 contextContent
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