from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.agent_invocation import AgentInvocation
from utils.logger import setup_logger
import uuid
import json
import time
from datetime import datetime

logger = setup_logger('agent_invocation_dao')

class AgentInvocationDAO:
    def __init__(self, db):
        self.db = db
    
    def create_invocation(self, user_id: str, agent_id: str, input_text: str, 
                         input_params: Optional[Dict] = None) -> AgentInvocation:
        """创建一个新的Agent调用记录"""
        session = self.db.get_session()
        try:
            invocation = AgentInvocation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                agent_id=agent_id,
                input_text=input_text,
                input_params=input_params,
                timestamps={},
                status='pending'
                # created_at 会自动设置为当前时间戳
            )
            
            # 设置session_id
            invocation.before_insert()
            
            session.add(invocation)
            session.commit()
            logger.info(f"创建Agent调用记录: {invocation.id}, agent_id: {agent_id}")
            return invocation
        except Exception as e:
            logger.error(f"创建Agent调用记录失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def start_invocation(self, invocation_id, input_params=None):
        """标记调用开始处理
        
        Args:
            invocation_id: 调用ID
            input_params: 可选的输入参数，用于更新调用的input_params
        """
        session = self.db.get_session()
        try:
            invocation = session.query(AgentInvocation).get(invocation_id)
            if invocation:
                invocation.set_start_time()
                # 如果提供了input_params，更新调用的input_params
                if input_params:
                    # 如果已有input_params，合并新的参数
                    if invocation.input_params:
                        invocation.input_params.update(input_params)
                    else:
                        invocation.input_params = input_params
                session.commit()
                logger.info(f"标记调用开始处理: {invocation_id}")
            else:
                logger.warning(f"未找到调用记录: {invocation_id}")
        except Exception as e:
            logger.error(f"标记调用开始处理失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def complete_invocation(self, invocation_id: str, success: bool = True, 
                           error: Optional[str] = None, 
                           metrics: Optional[Dict] = None) -> Optional[AgentInvocation]:
        """完成调用，设置结束时间和状态"""
        session = self.db.get_session()
        try:
            invocation = session.query(AgentInvocation).filter(
                AgentInvocation.id == invocation_id
            ).first()
            
            if not invocation:
                logger.warning(f"找不到调用记录: {invocation_id}")
                return None
            
            # 设置结束时间和状态
            invocation.set_end_time(success=success, error=error)
            
            # 更新额外的指标
            if metrics and isinstance(metrics, dict):
                if not invocation.metrics:
                    invocation.metrics = {}
                invocation.metrics.update(metrics)
            
            session.commit()
            logger.info(f"完成调用: {invocation_id}, 状态: {'成功' if success else '失败'}")
            return invocation
        except Exception as e:
            logger.error(f"完成调用失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_invocation(self, invocation_id: str) -> Optional[AgentInvocation]:
        """获取调用记录详情"""
        session = self.db.get_session()
        try:
            invocation = session.query(AgentInvocation).filter(
                AgentInvocation.id == invocation_id
            ).first()
            return invocation
        except Exception as e:
            logger.error(f"获取调用记录失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_session_invocations(self, session_id: str) -> List[AgentInvocation]:
        """获取同一会话的所有调用记录"""
        session = self.db.get_session()
        try:
            # 修改排序方式，按时间戳升序排序
            invocations = session.query(AgentInvocation).filter(
                AgentInvocation.session_id == session_id
            ).order_by(AgentInvocation.created_at.asc()).all()
            return invocations
        except Exception as e:
            logger.error(f"获取会话调用记录失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_user_invocations(self, user_id: str, limit: int = 20, offset: int = 0) -> List[AgentInvocation]:
        """获取用户的调用记录"""
        session = self.db.get_session()
        try:
            # 修改排序方式，按时间戳降序排序
            invocations = session.query(AgentInvocation).filter(
                AgentInvocation.user_id == user_id
            ).order_by(AgentInvocation.created_at.desc()).limit(limit).offset(offset).all()
            return invocations
        except Exception as e:
            logger.error(f"获取用户调用记录失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    # 可以添加一个新方法，用于获取特定时间范围内的调用记录
    def get_invocations_by_time_range(self, start_time: int, end_time: int, 
                                     user_id: Optional[str] = None) -> List[AgentInvocation]:
        """获取特定时间范围内的调用记录
        
        Args:
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            user_id: 可选的用户ID过滤
            
        Returns:
            符合条件的调用记录列表
        """
        session = self.db.get_session()
        try:
            query = session.query(AgentInvocation).filter(
                AgentInvocation.created_at >= start_time,
                AgentInvocation.created_at <= end_time
            )
            
            if user_id:
                query = query.filter(AgentInvocation.user_id == user_id)
                
            invocations = query.order_by(AgentInvocation.created_at.desc()).all()
            return invocations
        except Exception as e:
            logger.error(f"获取时间范围内调用记录失败: {str(e)}")
            raise e
        finally:
            session.close()

    def get_all_invocations(self, page=1, page_size=10, user_id=None, agent_id=None, status=None):
        """获取所有调用记录列表
        
        Args:
            page: 页码，默认为1
            page_size: 每页数量，默认为10
            user_id: 用户ID，如果提供则只返回该用户的记录
            agent_id: 根据Agent ID过滤，可选
            status: 根据状态过滤，可选
            
        Returns:
            tuple: (记录列表, 总数)
        """
        try:
            session = self.db.get_session()
            from database.agent_invocation import AgentInvocation
            
            query = session.query(AgentInvocation)
            
            # 应用过滤条件
            if user_id:
                query = query.filter(AgentInvocation.user_id == user_id)
            
            if agent_id:
                query = query.filter(AgentInvocation.agent_id == agent_id)
                
            if status:
                query = query.filter(AgentInvocation.status == status)
            
            # 获取总数
            total = query.count()
            
            # 分页
            offset = (page - 1) * page_size
            invocations = query.order_by(AgentInvocation.created_at.desc()).offset(offset).limit(page_size).all()
            
            return invocations, total
        except Exception as e:
            logger.error(f"获取所有调用记录列表失败: {str(e)}")
            return [], 0
        finally:
            if 'session' in locals():
                session.close()
    
    def get_invocation_by_id(self, invocation_id):
        """获取指定ID的调用记录详情
        
        Args:
            invocation_id: 调用记录ID
            
        Returns:
            AgentInvocation: 调用记录对象
        """
        try:
            session = self.db.get_session()
            invocation = session.query(AgentInvocation).filter(AgentInvocation.id == invocation_id).first()
            return invocation
        except Exception as e:
            logger.error(f"获取调用记录详情失败: {str(e)}")
            return None
        finally:
            if 'session' in locals():
                session.close()