from database.models import SearchResultModel, SearchQueryModel
from models.search_result import SearchResult
from utils.logger import setup_logger

logger = setup_logger('search_dao')

class SearchDAO:
    def __init__(self, db):
        self.db = db
    
    async def save_search_results(self, query, results):
        """保存搜索结果到数据库"""
        try:
            session = self.db.get_session()
            try:
                # 先保存查询
                query_model = SearchQueryModel(query_text=query)
                session.add(query_model)
                session.flush()  # 获取自增ID
                
                # 保存搜索结果
                for result in results:
                    result_model = SearchResultModel(
                        key_id=str(result.key_id),
                        title=result.title,
                        content=result.content,
                        snippet=result.snippet,
                        link=result.link,
                        source=result.source,
                        type=result.type,
                        thumbnail_link=getattr(result, 'thumbnail_link', None),
                        context_link=getattr(result, 'context_link', None),
                        query_id=query_model.id
                    )
                    session.add(result_model)
                
                session.commit()
                logger.info(f"保存搜索结果成功，查询: {query}, 结果数量: {len(results)}")
                return True
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
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