from typing import Dict, Any, List, Tuple, Optional
from utils.logger import setup_logger

logger = setup_logger('tool_factory')

class ToolFactory:
    """工具工厂类，用于创建和调用不同类型的工具服务"""
    
    @staticmethod
    async def create_and_invoke_tools(tools: List[Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        根据工具列表创建并调用相应的工具服务
        
        Args:
            tools: 工具对象列表
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: 工具服务实例字典和工具调用结果字典
        """
        tool_services = {}
        tool_results = {}
        
        if not tools:
            logger.info("没有配置工具，跳过工具初始化")
            return tool_results
        
        for tool in tools:
            tool_name = tool.name.lower() if hasattr(tool, 'name') else ""
            
            # 搜索工具
            if "google search" in tool_name or "搜索" in tool_name:
                await ToolFactory._init_search_tool(tool_services, tool_results)
            
            # 新闻工具
            elif "news" in tool_name or "新闻" in tool_name:
                await ToolFactory._init_news_tool(tool_services, tool_results)
            
            # 可以继续添加其他工具类型
            
            else:
                logger.info(f"未知工具类型: {tool_name}，跳过初始化")
        
        return tool_results
    
    @staticmethod
    async def _init_search_tool(tool_services: Dict[str, Any], tool_results: Dict[str, Any]):
        """初始化搜索工具"""
        try:
            from services.google_search_service import GoogleSearchService
            search_service = GoogleSearchService()
            tool_services["google_search"] = search_service
            
            # 执行搜索并获取结果
            search_results = await search_service.search("latest technology news")
            tool_results["google_search"] = search_results
            logger.info("Google搜索工具初始化并调用成功")
        except Exception as e:
            logger.error(f"初始化或调用Google搜索工具失败: {str(e)}")
            tool_results["google_search"] = f"搜索工具调用失败: {str(e)}"
    
    @staticmethod
    async def _init_news_tool(tool_services: Dict[str, Any], tool_results: Dict[str, Any]):
        """初始化新闻工具"""
        try:
            from services.bbc_service import BBCService
            from services.wired_news_service import WiredNewsService
            
            # 初始化BBC新闻服务
            try:
                bbc_service = BBCService()
                tool_services["bbc_news"] = bbc_service
                bbc_news = await bbc_service.get_latest_news()
                tool_results["bbc_news"] = bbc_news
                logger.info("BBC新闻工具初始化并调用成功")
            except Exception as bbc_error:
                logger.error(f"初始化或调用BBC新闻工具失败: {str(bbc_error)}")
                tool_results["bbc_news"] = f"BBC新闻工具调用失败: {str(bbc_error)}"
            
            # 初始化Wired新闻服务
            try:
                wired_service = WiredNewsService()
                tool_services["wired_news"] = wired_service
                wired_news = await wired_service.get_latest_news()
                tool_results["wired_news"] = wired_news
                logger.info("Wired新闻工具初始化并调用成功")
            except Exception as wired_error:
                logger.error(f"初始化或调用Wired新闻工具失败: {str(wired_error)}")
                tool_results["wired_news"] = f"Wired新闻工具调用失败: {str(wired_error)}"
                
        except Exception as e:
            logger.error(f"初始化新闻工具失败: {str(e)}")
            tool_results["news"] = f"新闻工具初始化失败: {str(e)}"