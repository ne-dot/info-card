from typing import Dict, Any, List, Tuple, Optional
from utils.logger import setup_logger

logger = setup_logger('tool_factory')

class ToolFactory:
    """工具工厂类，用于创建和调用不同类型的工具服务"""
    
    @staticmethod
    async def create_and_invoke_tools(tools: List[Any], query: str = None, db = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        根据工具列表创建并调用相应的工具服务
        
        Args:
            tools: 工具对象列表
            query: 查询字符串，默认为None
            db: 数据库连接，默认为None
                
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: 工具服务实例字典和工具调用结果字典
        """
        tool_services = {}
        tool_results = {}
        
        if not tools:
            logger.info("没有配置工具，跳过工具初始化")
            return {}, {}
        
        # 如果没有提供查询，使用默认查询
        if not query:
            query = "latest technology news"
        
        for tool in tools:
            tool_name = tool.name.lower() if hasattr(tool, 'name') else ""
            
            # Google搜索工具
            if "google search" in tool_name or "搜索" in tool_name:
                await ToolFactory._init_google_search_tool(tool_services, tool_results, query, db)
            
            # 科技新闻工具
            elif "tech news" in tool_name or "科技新闻" in tool_name:
                await ToolFactory._init_tech_news_tool(tool_services, tool_results, query, db)
            
            # 建议工具
            elif "suggestion" in tool_name or "建议" in tool_name:
                await ToolFactory._init_suggestion_tool(tool_services, tool_results, query, db)
            
            # 可以继续添加其他工具类型
            else:
                logger.info(f"未知工具类型: {tool_name}，跳过初始化")
        
        return tool_services, tool_results
    
    @staticmethod
    async def _init_google_search_tool(tool_services: Dict[str, Any], tool_results: Dict[str, Any], query: str, db = None):
        """初始化Google搜索工具"""
        try:
            from services.google_search_service import GoogleSearchService
            
            # 初始化Google搜索服务，传递数据库连接
            search_service = GoogleSearchService(db=db)
            tool_services["google_search"] = search_service
            
            # 执行搜索并获取结果
            search_results = await search_service.get_tool_data(query)
            tool_results["google_search"] = search_results
            logger.info(f"Google搜索工具初始化并调用成功，查询: {query}")
        except IndentationError as ie:
            # 专门处理缩进错误
            error_msg = f"缩进错误: {str(ie)}"
            logger.error(f"初始化或调用Google搜索工具失败: {error_msg}")
            tool_results["google_search"] = {"error": error_msg}
        except ImportError as imp_e:
            # 处理导入错误
            error_msg = f"导入错误: {str(imp_e)}"
            logger.error(f"初始化或调用Google搜索工具失败: {error_msg}")
            tool_results["google_search"] = {"error": error_msg}
        except Exception as e:
            # 处理其他错误
            error_msg = f"错误: {str(e)}"
            logger.error(f"初始化或调用Google搜索工具失败: {error_msg}")
            tool_results["google_search"] = {"error": error_msg}
    
    @staticmethod
    async def _init_tech_news_tool(tool_services: Dict[str, Any], tool_results: Dict[str, Any], query: str, db = None):
        """初始化科技新闻工具"""
        try:
            from services.tech_news_service import TechNewsService
            
            # 初始化科技新闻服务，传递数据库连接
            tech_news_service = TechNewsService(db=db)
            tool_services["tech_news"] = tech_news_service
            
            # 获取科技新闻并返回结果
            news_results = await tech_news_service.get_tool_data(query)
            tool_results["tech_news"] = news_results
            logger.info(f"科技新闻工具初始化并调用成功，查询: {query}")
        except Exception as e:
            logger.error(f"初始化或调用科技新闻工具失败: {str(e)}")
            tool_results["tech_news"] = {"error": f"科技新闻工具调用失败: {str(e)}"}
    
    @staticmethod
    async def _init_suggestion_tool(tool_services: Dict[str, Any], tool_results: Dict[str, Any], query: str, db = None):
        """初始化建议工具"""
        try:
            from services.suggestion_service import SuggestionService
            
            # 初始化建议服务，传递数据库连接
            suggestion_service = SuggestionService(db=db)
            tool_services["suggestion"] = suggestion_service
            
            # 获取建议数据
            suggestion_data = await suggestion_service.get_tool_data(query)
            tool_results["suggestion"] = suggestion_data
            logger.info(f"建议工具初始化并调用成功，查询: {query}")
        except Exception as e:
            logger.error(f"初始化或调用建议工具失败: {str(e)}")
            tool_results["suggestion"] = {"error": f"建议工具调用失败: {str(e)}"}
    
    @staticmethod
    async def save_tool_results(tool_results: Dict[str, Any], tool_services: Dict[str, Any], invocation_id: str, result: str = None, **kwargs):
        """
        保存工具调用结果
        
        Args:
            tool_results: 工具调用结果字典
            tool_services: 工具服务实例字典
            invocation_id: 调用ID
            result: AI生成的结果
            **kwargs: 其他参数
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not tool_results or not tool_services:
                logger.info("没有工具结果或工具服务，跳过保存")
                return False
                
            success_count = 0
            
            # 遍历所有工具结果
            for tool_name, result_data in tool_results.items():
                # 获取对应的工具服务
                service = tool_services.get(tool_name)
                
                if service and hasattr(service, 'save_tool_data'):
                    # 调用服务的save_tool_data方法
                    try:
                        # 合并kwargs，添加invocation_id
                        save_kwargs = {**kwargs, 'invocation_id': invocation_id}
                        
                        # 调用保存方法
                        save_success = await service.save_tool_data(result_data, result, **save_kwargs)
                        
                        if save_success:
                            success_count += 1
                            logger.info(f"成功保存 {tool_name} 的工具数据")
                        else:
                            logger.warning(f"保存 {tool_name} 的工具数据失败")
                    except Exception as e:
                        logger.error(f"调用 {tool_name} 的save_tool_data方法失败: {str(e)}")
                else:
                    logger.warning(f"工具 {tool_name} 没有save_tool_data方法或服务不存在，跳过保存")
            
            logger.info(f"共成功保存 {success_count}/{len(tool_results)} 个工具的数据")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"保存工具调用结果失败: {str(e)}")
            return False
    
    @staticmethod
    def build_tool_prompt(tool_results: Dict[str, Any], tool_services: Dict[str, Any], base_prompt: str, lang: str = 'zh', query: str = None) -> Tuple[str, str]:
        """
        构建包含工具结果的完整提示词
        
        Args:
            tool_results: 工具调用结果字典
            tool_services: 工具服务实例字典
            base_prompt: 基础提示词
            lang: 语言，默认为中文
            query: 用户查询，默认为None
            
        Returns:
            Tuple[str, str]: 包含(system_prompt, human_message)的元组
        """
        # 如果没有工具结果，直接返回基础提示词和包含查询的人类消息
        if not tool_results or not tool_services:
            if query:
                # 根据语言构建包含查询的人类消息
                human_message = f"我的问题是：{query}" if lang.startswith('zh') else f"My question is: {query}"
                return base_prompt, human_message
            else:
                default_human_message = "请根据以上信息提供回复" if lang.startswith('zh') else "Please provide a response based on the information above"
                return base_prompt, default_human_message
        
        # 初始化系统提示词为基础提示词
        system_prompt = base_prompt
        human_messages = []
        
        # 处理每个工具的结果
        for tool_name, result in tool_results.items():
            # 获取对应的工具服务
            service = tool_services.get(tool_name)
            
            if service and hasattr(service, 'organize_prompt'):
                # 调用服务的organize_prompt方法
                try:
                    tool_system_prompt, tool_human_message = service.organize_prompt(result, lang, base_prompt)
                    
                    # 添加工具系统提示词到总系统提示词
                    if tool_system_prompt:
                        system_prompt += f"\n\n## {tool_name} 结果:\n{tool_system_prompt}"
                    
                    # 添加工具人类消息到人类消息列表
                    if tool_human_message:
                        human_messages.append(tool_human_message)
                        
                except Exception as e:
                    logger.error(f"调用 {tool_name} 的organize_prompt方法失败: {str(e)}")
                    # 添加错误信息到系统提示词
                    system_prompt += f"\n\n## {tool_name} 结果:\n错误: {str(e)}"
            else:
                # 如果没有organize_prompt方法，使用默认格式
                if isinstance(result, dict) and 'error' in result:
                    error_msg = result['error']
                    system_prompt += f"\n\n## {tool_name} 结果:\n错误: {error_msg}"
                else:
                    # 简单格式化结果
                    system_prompt += f"\n\n## {tool_name} 结果:\n{str(result)}"
        
        # 如果没有人类消息，使用默认消息
        if not human_messages:
            final_human_message = "请根据以上信息提供回复" if lang.startswith('zh') else "Please provide a response based on the information above"
        else:
            final_human_message = "\n".join(human_messages)
        
        return system_prompt, final_human_message