from typing import Dict, List, Optional, Tuple, Any
from utils.logger import setup_logger
from dao.agent_invocation_dao import AgentInvocationDAO
from dao.agent_dao import AgentDAO

logger = setup_logger('invocation_service')

class InvocationService:
    """调用记录服务，处理与Agent调用记录相关的业务逻辑"""
    
    def __init__(self, db):
        """初始化调用记录服务
        
        Args:
            db: 数据库连接实例
        """
        self.db = db
        self.agent_invocation_dao = AgentInvocationDAO(db)
        self.agent_dao = AgentDAO(db)
    
    async def get_all_invocations(self, page=1, page_size=10, user_id=None, agent_id=None, status=None):
        """获取所有调用记录列表
        
        Args:
            page: 页码
            page_size: 每页数量
            user_id: 用户ID，如果提供则只返回该用户的记录
            agent_id: 根据Agent ID过滤，可选
            status: 根据状态过滤，可选
            
        Returns:
            dict: 包含调用记录列表和分页信息
        """
        try:
            # 获取调用记录列表
            invocations, total = self.agent_invocation_dao.get_all_invocations(
                page, page_size, user_id, agent_id, status
            )
            
            # 转换为字典列表
            invocation_list = []
            for inv in invocations:
                inv_dict = inv.to_dict() if hasattr(inv, 'to_dict') else {
                    "id": inv.id,
                    "user_id": inv.user_id,
                    "agent_id": inv.agent_id,
                    "session_id": inv.session_id,
                    "input_text": inv.input_text,
                    "status": inv.status,
                    "created_at": inv.created_at,
                    "timestamps": inv.timestamps,
                    "metrics": inv.metrics,
                    "error_logs": inv.error_logs
                }
                
                # 为每个调用记录添加Agent信息
                agent = self.agent_dao.get_agent_by_key_id(inv.agent_id)
                if agent:
                    inv_dict["agent"] = {
                        "id": agent.key_id,
                        "name": agent.name,
                        "type": agent.type
                    }
                
                invocation_list.append(inv_dict)
            
            return {
                "invocations": invocation_list,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"获取所有调用记录列表失败: {str(e)}")
            raise Exception(f"获取所有调用记录列表失败: {str(e)}")
    
    async def get_invocation_detail(self, invocation_id, user_id=None):
        """获取调用记录详情
        
        Args:
            invocation_id: 调用记录ID
            user_id: 用户ID，用于权限检查
            
        Returns:
            dict: 调用记录详情
        """
        try:
            # 获取调用记录
            invocation = self.agent_invocation_dao.get_invocation_by_id(invocation_id)
            if not invocation:
                raise Exception(f"找不到ID为{invocation_id}的调用记录")
            
            # 权限检查
            if user_id and invocation.user_id != user_id:
                # 检查是否为Agent创建者
                agent = self.agent_dao.get_agent_by_key_id(invocation.agent_id)
                if not agent or agent.user_id != user_id:
                    raise Exception("您没有权限查看此调用记录")
            
            # 转换为字典
            invocation_dict = invocation.to_dict() if hasattr(invocation, 'to_dict') else {
                "id": invocation.id,
                "user_id": invocation.user_id,
                "agent_id": invocation.agent_id,
                "session_id": invocation.session_id,
                "input_text": invocation.input_text,
                "status": invocation.status,
                "created_at": invocation.created_at,
                "timestamps": invocation.timestamps,
                "metrics": invocation.metrics,
                "error_logs": invocation.error_logs
            }
            
            # 获取关联的Agent信息
            agent = self.agent_dao.get_agent_by_key_id(invocation.agent_id)
            if agent:
                invocation_dict["agent"] = {
                    "id": agent.key_id,
                    "name": agent.name,
                    "type": agent.type
                }
            
            return {
                "invocation": invocation_dict
            }
        except Exception as e:
            logger.error(f"获取调用记录详情失败: {str(e)}")
            raise Exception(f"获取调用记录详情失败: {str(e)}")