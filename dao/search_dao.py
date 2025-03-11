from database.models import SearchResultModel, SearchQueryModel
from models.search_result import SearchResult
from utils.logger import setup_logger
import time
import uuid

logger = setup_logger('search_dao')

class SearchDAO:
    def __init__(self, db):
        self.db = db
    
    async def save_search_results(self, query, results, user_id=None, anonymous_id=None):
        """保存搜索结果到数据库，支持匿名用户和非匿名用户"""
        try:
            session = self.db.get_session()
            try:
                # 创建搜索查询记录
                from database.models import SearchQueryModel
                search_query = SearchQueryModel(
                    query_text=query,
                    date=int(time.time()),  # 这里使用了 time 模块
                    user_id=user_id,
                    anonymous_id=anonymous_id
                )
                
                session.add(search_query)
                session.flush()  # 获取自增ID
                
                # 保存搜索结果
                from database.models import SearchResultModel
                for result in results:
                    # 生成唯一ID
                    key_id = str(uuid.uuid4())
                    
                    db_result = SearchResultModel(
                        key_id=key_id,
                        title=result.title,
                        content=result.content,
                        snippet=result.snippet if hasattr(result, 'snippet') else None,
                        link=result.link,
                        source=result.source if hasattr(result, 'source') else None,
                        type=result.type,
                        thumbnail_link=getattr(result, 'thumbnail_link', None),
                        context_link=getattr(result, 'context_link', None),
                        query_id=search_query.id,
                        date=int(time.time()),
                        user_id=user_id,
                        anonymous_id=anonymous_id
                    )
                    session.add(db_result)
                
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            from utils.logger import setup_logger
            logger = setup_logger('search_dao')
            logger.error(f"保存搜索结果失败: {str(e)}")
            return False
    
    async def get_search_results_by_query(self, query):
        """通过查询文本获取搜索结果"""
        try:
            session = self.db.get_session()
            try:
                # 查找最近的查询
                query_model = session.query(SearchQueryModel).filter(
                    SearchQueryModel.query_text == query
                ).order_by(SearchQueryModel.date.desc()).first()
                
                if not query_model:
                    return []
                
                # 获取关联的搜索结果
                result_models = session.query(SearchResultModel).filter(
                    SearchResultModel.query_id == query_model.id
                ).all()
                
                # 转换为领域模型
                results = []
                for model in result_models:
                    result = SearchResult(
                        title=model.title,
                        content=model.content,
                        snippet=model.snippet,
                        link=model.link,
                        source=model.source,
                        type=model.type,
                        thumbnail_link=model.thumbnail_link,
                        context_link=model.context_link
                    )
                    result.key_id = model.key_id
                    result.date = model.date
                    results.append(result)
                
                return results
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取搜索结果失败: {str(e)}")
            return []