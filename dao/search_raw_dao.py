from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.search_raw_data import SearchRawData
from utils.logger import setup_logger
import uuid
import time
import json

logger = setup_logger('search_raw_dao')

class SearchRawDAO:
    def __init__(self, db):
        self.db = db
    
    def create_search_data(self, invocation_id: str, engine_type: str, 
                          content_type: str, request_data: Dict, 
                          response_data: Any, structured_data: Optional[Dict] = None,
                          cache_info: Optional[Dict] = None) -> SearchRawData:
        """创建搜索引擎数据记录
        
        Args:
            invocation_id: 关联的调用ID
            engine_type: 搜索引擎类型，如google/bing等
            content_type: 内容类型，如text/image/mixed
            request_data: 请求参数
            response_data: 响应数据
            structured_data: 结构化结果
            cache_info: 缓存信息
            
        Returns:
            创建的搜索数据记录
        """
        session = self.db.get_session()
        try:
            search_data = SearchRawData(
                id=str(uuid.uuid4()),
                invocation_id=invocation_id,
                engine_type=engine_type,
                content_type=content_type,
                request=request_data,
                structured_data=structured_data,
                cache_info=cache_info
            )
            
            # 设置响应数据（自动压缩）
            search_data.set_response(response_data)
            
            session.add(search_data)
            session.commit()
            logger.info(f"创建搜索数据: {search_data.id}, 调用ID: {invocation_id}, 引擎: {engine_type}")
            return search_data
        except Exception as e:
            logger.error(f"创建搜索数据失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_search_data(self, search_id: str) -> Optional[SearchRawData]:
        """获取搜索数据详情
        
        Args:
            search_id: 搜索数据ID
            
        Returns:
            搜索数据记录，如果不存在则返回None
        """
        session = self.db.get_session()
        try:
            search_data = session.query(SearchRawData).filter(
                SearchRawData.id == search_id
            ).first()
            return search_data
        except Exception as e:
            logger.error(f"获取搜索数据失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def get_invocation_search_data(self, invocation_id: str) -> List[SearchRawData]:
        """获取调用相关的所有搜索数据
        
        Args:
            invocation_id: 调用ID
            
        Returns:
            搜索数据记录列表
        """
        session = self.db.get_session()
        try:
            search_data_list = session.query(SearchRawData).filter(
                SearchRawData.invocation_id == invocation_id
            ).order_by(SearchRawData.created_at.desc()).all()
            return search_data_list
        except Exception as e:
            logger.error(f"获取调用搜索数据失败: {str(e)}")
            raise e
        finally:
            session.close()
    
    def update_structured_data(self, search_id: str, structured_data: Dict) -> Optional[SearchRawData]:
        """更新搜索数据的结构化结果
        
        Args:
            search_id: 搜索数据ID
            structured_data: 结构化结果
            
        Returns:
            更新后的搜索数据记录，如果不存在则返回None
        """
        session = self.db.get_session()
        try:
            search_data = session.query(SearchRawData).filter(
                SearchRawData.id == search_id
            ).first()
            
            if not search_data:
                logger.warning(f"找不到搜索数据: {search_id}")
                return None
            
            search_data.structured_data = structured_data
            session.commit()
            logger.info(f"更新搜索数据结构化结果: {search_id}")
            return search_data
        except Exception as e:
            logger.error(f"更新搜索数据结构化结果失败: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()