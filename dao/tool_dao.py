from database.tool_models import Tool
from utils.logger import setup_logger

logger = setup_logger('tool_dao')

class ToolDAO:
    def __init__(self, db):
        self.db = db
        
    async def create_tool(self, name, tool_type, endpoint=None, description=None, config_params=None):
        """创建新工具"""
        try:
            session = self.db.get_session()
            tool = Tool(
                name=name,
                tool_type=tool_type,
                endpoint=endpoint,
                description=description,
                config_params=config_params,
                is_enabled=True
            )
            session.add(tool)
            session.commit()
            
            # 在提交后刷新对象，确保所有属性都已加载
            session.refresh(tool)
            
            # 打印出Tool里面所有的值
            logger.debug(f"Tool对象: {tool.__dict__}")
            
            # 创建一个包含所有需要的属性的字典
            tool_dict = {
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
            
            # 打印出转换后的字典
            logger.debug(f"转换后的字典: {tool_dict}")
            
            logger.info(f"创建工具成功: {name}")
            return tool_dict  # 返回字典而不是 SQLAlchemy 对象
        except Exception as e:
            session.rollback()
            logger.error(f"创建工具失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    async def get_tool_by_id(self, tool_id):
        """根据ID获取工具"""
        try:
            session = self.db.get_session()
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                return None
                
            # 转换为字典
            tool_dict = {
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
            return tool_dict
        except Exception as e:
            logger.error(f"获取工具失败: {str(e)}")
            return None
        finally:
            session.close()
            
    async def get_all_tools(self, page=1, page_size=10):
        """获取所有工具，支持分页
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
        
        Returns:
            tuple: (工具列表, 总数量)
        """
        try:
            session = self.db.get_session()
            
            # 计算总数
            total = session.query(Tool).count()
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询分页数据
            tools = session.query(Tool).order_by(Tool.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 转换为字典列表
            tools_dict = []
            for tool in tools:
                tool_dict = {
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
                tools_dict.append(tool_dict)
                
            return tools_dict, total
        except Exception as e:
            logger.error(f"获取所有工具失败: {str(e)}")
            return [], 0
        finally:
            session.close()
            
    async def update_tool(self, tool_id, **kwargs):
        """更新工具信息"""
        try:
            session = self.db.get_session()
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                logger.warning(f"工具不存在: {tool_id}")
                return None
                
            # 更新工具属性
            for key, value in kwargs.items():
                if hasattr(tool, key):
                    setattr(tool, key, value)
                    
            session.commit()
            session.refresh(tool)
            
            # 转换为字典
            tool_dict = {
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
            
            logger.info(f"更新工具成功: {tool_id}")
            return tool_dict
        except Exception as e:
            session.rollback()
            logger.error(f"更新工具失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    async def delete_tool(self, tool_id):
        """删除工具"""
        try:
            session = self.db.get_session()
            tool = session.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                logger.warning(f"工具不存在: {tool_id}")
                return False
                
            session.delete(tool)
            session.commit()
            logger.info(f"删除工具成功: {tool_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"删除工具失败: {str(e)}")
            raise e
        finally:
            session.close()