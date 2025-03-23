from typing import Dict, Any, Tuple, Protocol

class ToolProtocol(Protocol):
    """工具协议，定义了工具服务需要实现的接口"""
    
    @property
    def tool_name(self) -> str:
        """工具名称"""
        ...
    
    @property
    def tool_description(self) -> str:
        """工具描述"""
        ...
    
    async def get_tool_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        获取工具数据
        
        Args:
            query: 查询字符串
            **kwargs: 其他参数
                
        Returns:
            Dict[str, Any]: 工具数据
        """
        ...
    
    def organize_prompt(self, data: Dict[str, Any], lang: str = 'en', prompt: str = None, base_prompt: str = None) -> Tuple[str, str]:
        """
        根据工具数据组织提示词
        
        Args:
            data: 工具数据
            lang: 语言，默认为英文
            prompt: 自定义系统提示词，如果提供则使用此提示词
            base_prompt: 基础提示词，如果提供则与工具提示词结合
            
        Returns:
            Tuple[str, str]: 包含(system_prompt, human_message)的元组
        """
        ...
    
    async def save_tool_data(self, data: Dict[str, Any], result: str, **kwargs) -> bool:
        """
        保存工具数据和处理结果
        
        Args:
            data: 工具数据，通常是get_tool_data的返回值
            result: 处理结果，通常是AI生成的回复
            **kwargs: 其他参数，可能包含user_id, invocation_id等
            
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        ...