from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.ai_summary import AISummary
from utils.logger import setup_logger
import uuid
import time

logger = setup_logger('ai_summary_dao')

class AISummaryDAO:
    def __init__(self, db):
        self.db = db
    
    # Update the create_summary method
    def create_summary(self, invocation_id: str, content: str, 
                      metadata: Dict, version_chain: Optional[Dict] = None) -> AISummary:
        """创建AI总结记录
        
        Args:
            invocation_id: 关联的调用ID
            content: 总结内容
            metadata: 元数据，包含模型信息、质量评分等
            version_chain: 版本链结构
            
        Returns:
            创建的AI总结记录
        """
        session = self.db.get_session()
        try:
            summary = AISummary(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                content=content,
                meta_info=metadata,  # Changed from metadata to meta_info
                version_chain=version_chain
            )
            
            session.add(summary)
            session.commit()
            logger.info(f"创建AI总结: {summary.id}, 调用ID: {invocation_id}")
            return summary
        except Exception as e:
            logger.error(f"创建AI总结失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Also update the update_summary_content method
    def update_summary_content(self, summary_id: str, content: str, 
                              update_metadata: Optional[Dict] = None) -> Optional[AISummary]:
        """更新AI总结内容
        
        Args:
            summary_id: 总结ID
            content: 新的总结内容
            update_metadata: 需要更新的元数据
            
        Returns:
            更新后的AI总结记录，如果不存在则返回None
        """
        session = self.db.get_session()
        try:
            summary = session.query(AISummary).filter(
                AISummary.id == summary_id
            ).first()
            
            if not summary:
                logger.warning(f"找不到AI总结: {summary_id}")
                return None
            
            # 更新内容
            summary.content = content
            
            # 更新元数据
            if update_metadata and isinstance(update_metadata, dict):
                if not summary.meta_info:  # Changed from metadata to meta_info
                    summary.meta_info = {}
                summary.meta_info.update(update_metadata)
            
            # 如果有版本链，更新版本信息
            if summary.version_chain:
                if not isinstance(summary.version_chain, dict):
                    summary.version_chain = {}
                
                # 添加新版本记录
                version_id = f"v{len(summary.version_chain.get('versions', [])) + 1}"
                if 'versions' not in summary.version_chain:
                    summary.version_chain['versions'] = []
                
                summary.version_chain['versions'].append({
                    'id': version_id,
                    'timestamp': int(time.time() * 1000),
                    'changes': update_metadata.get('change_reason', '内容更新') if update_metadata else '内容更新'
                })
                
                summary.version_chain['current'] = version_id
            
            session.commit()
            logger.info(f"更新AI总结内容: {summary_id}")
            return summary
        except Exception as e:
            logger.error(f"更新AI总结内容失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_summaries_by_time_range(self, start_time: int, end_time: int) -> List[AISummary]:
        """获取特定时间范围内的AI总结
        
        Args:
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            
        Returns:
            符合条件的AI总结列表
        """
        session = self.db.get_session()
        try:
            summaries = session.query(AISummary).filter(
                AISummary.created_at >= start_time,
                AISummary.created_at <= end_time
            ).order_by(AISummary.created_at.desc()).all()
            return summaries
        except Exception as e:
            logger.error(f"获取时间范围内AI总结失败: {str(e)}")
            raise e
        finally:
            session.close()