from dao.tool_dao import ToolDAO
from utils.logger import setup_logger
from utils.response_utils import ErrorCode

logger = setup_logger('tool_service')

class ToolService:
    def __init__(self, db):
        self.db = db
        self.tool_dao = ToolDAO(db)
        
    # 修改 create_tool 方法，确保不再调用 _convert_tool_to_dict
    async def create_tool(self, name, tool_type, endpoint=None, description=None, config_params=None):
        """创建新工具"""
        try:
            tool_dict = await self.tool_dao.create_tool(
                name=name,
                tool_type=tool_type,
                endpoint=endpoint,
                description=description,
                config_params=config_params
            )
            # 直接返回字典，不需要转换
            return tool_dict, None, None
        except Exception as e:
            logger.error(f"创建工具服务失败: {str(e)}")
            return None, f"创建工具失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def get_tool(self, tool_id):
        """获取工具详情"""
        try:
            tool_dict = await self.tool_dao.get_tool_by_id(tool_id)
            if not tool_dict:
                return None, "工具不存在", ErrorCode.RESOURCE_NOT_FOUND
            return tool_dict, None, None
        except Exception as e:
            logger.error(f"获取工具服务失败: {str(e)}")
            return None, f"获取工具失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def get_all_tools(self, page=1, page_size=10):
        """获取所有工具，支持分页
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            tuple: (工具列表, 总数量, 错误信息, 错误码)
        """
        try:
            tools_dict, total = await self.tool_dao.get_all_tools(page, page_size)
            return tools_dict, total, None, None
        except Exception as e:
            logger.error(f"获取所有工具服务失败: {str(e)}")
            return None, 0, f"获取所有工具失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def update_tool(self, tool_id, **kwargs):
        """更新工具信息"""
        try:
            tool_dict = await self.tool_dao.update_tool(tool_id, **kwargs)
            if not tool_dict:
                return None, "工具不存在", ErrorCode.RESOURCE_NOT_FOUND
            return tool_dict, None, None
        except Exception as e:
            logger.error(f"更新工具服务失败: {str(e)}")
            return None, f"更新工具失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def delete_tool(self, tool_id):
        """删除工具"""
        try:
            result = await self.tool_dao.delete_tool(tool_id)
            if not result:
                return False, "工具不存在", ErrorCode.RESOURCE_NOT_FOUND
            return True, None, None
        except Exception as e:
            logger.error(f"删除工具服务失败: {str(e)}")
            return False, f"删除工具失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    # 在 ToolService 类中添加新方法
    async def get_tool_types(self):
        """获取所有可用的工具类型"""
        try:
            # 从数据库模型中获取工具类型枚举值
            from sqlalchemy import inspect
            from database.tool_models import Tool
            
            inspector = inspect(Tool)
            tool_type_column = inspector.columns.get('tool_type')
            enum_values = tool_type_column.type.enums
            
            # 构建响应数据
            tool_types = {value: value for value in enum_values}
            
            return tool_types, None, None
        except Exception as e:
            logger.error(f"获取工具类型服务失败: {str(e)}")
            return None, f"获取工具类型失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    def _convert_tool_to_dict(self, tool):
        """将 Tool 对象转换为字典"""
        if not tool:
            return None
        return {
            "id": tool.id,
            "name": tool.name,
            "tool_type": tool.tool_type,
            "endpoint": tool.endpoint,
            "description": tool.description,
            "config_params": tool.config_params,
            "is_enabled": tool.is_enabled,
            "created_at": tool.created_at,
            "updated_at": tool.updated_at
        }