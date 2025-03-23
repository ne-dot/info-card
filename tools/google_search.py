from langchain_google_community import GoogleSearchAPIWrapper
from utils.logger import setup_logger
from config.settings import GOOGLE_API_KEY, GOOGLE_CSE_ID
import json
import requests
from functools import lru_cache
from typing import List, Dict, Any  # Add this import

logger = setup_logger('google_search')

@lru_cache(maxsize=1)
def get_google_search():
    return GoogleSearchAPIWrapper(
        google_api_key=GOOGLE_API_KEY,
        google_cse_id=GOOGLE_CSE_ID
    )

async def search_google_by_text(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    使用Google搜索文本内容
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制，默认为5
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        logger.info(f"开始 Google 文本搜索: {query}")
        
        search = get_google_search()
        logger.info(f"Google API 配置: API_KEY={GOOGLE_API_KEY[:4]}..., CSE_ID={GOOGLE_CSE_ID[:4]}...")
        
        raw_results = search.results(query, num_results=5)
        logger.info(f"原始结果数量: {len(raw_results) if raw_results else 0}")
        
        formatted_results = []
        for result in raw_results:
            formatted_result = {
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('link', ''),
                'source': 'google'
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"文本搜索结果数量: {len(formatted_results)}")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    except Exception as e:
        logger.error(f"Google 文本搜索失败: {str(e)}")
        logger.exception("详细错误信息")
        # 返回空列表而不是抛出异常，确保程序可以继续运行
        return []

async def search_google_by_image(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    使用Google搜索图片内容
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制，默认为5
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        logger.info(f"开始 Google 图片搜索: {query}")
        logger.info(f"Google API 配置: API_KEY={GOOGLE_API_KEY[:4]}..., CSE_ID={GOOGLE_CSE_ID[:4]}...")
        
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

        logger.info(f"发送图片搜索请求: {search_url}")
        response = requests.get(search_url, params=params)
        logger.info(f"图片搜索响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"图片搜索请求失败: {response.text}")
            return []
            
        results = response.json()
        logger.info(f"图片搜索原始响应: {json.dumps(results, ensure_ascii=False)[:500]}...")
        
        formatted_results = []
        if "items" in results:
            logger.info(f"找到 {len(results['items'])} 个图片结果")
            # 收集所有需要搜索上下文的 URL
            context_urls = [item.get('image', {}).get('contextLink') 
                          for item in results['items'] 
                          if item.get('image', {}).get('contextLink')]
            
            logger.info(f"需要获取上下文的URL数量: {len(context_urls)}")
            
            # 批量获取上下文内容
            context_contents = {}
            if context_urls:
                for context_url in context_urls:
                    try:
                        # 对每个 URL 单独搜索，确保能获取到内容
                        logger.info(f"获取上下文内容: {context_url}")
                        context_results = search.results(f"site:{context_url}", num_results=1)
                        if context_results:
                            context_contents[context_url] = context_results[0].get('snippet', '')
                            logger.info(f"成功获取上下文: {context_url}")
                        else:
                            logger.warning(f"未找到上下文内容: {context_url}")
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
        else:
            logger.warning(f"图片搜索未返回任何结果，响应内容: {json.dumps(results, ensure_ascii=False)}")
        
        logger.info(f"图片搜索结果数量: {len(formatted_results)}")
        logger.info("-" * 50)
        logger.info(json.dumps(formatted_results, ensure_ascii=False, indent=2))
        logger.info("-" * 50)
        
        return formatted_results
    except Exception as e:
        logger.error(f"Google 图片搜索失败: {str(e)}")
        logger.exception("详细错误信息")
        # 返回空列表而不是抛出异常
        return []