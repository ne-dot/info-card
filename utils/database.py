from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.search_result_dbmodel import Base, SearchResultModel
from utils.logger import setup_logger

logger = setup_logger('database')

class Database:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

    def init_database(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据表初始化成功")
        except Exception as e:
            logger.error(f"数据表初始化失败: {str(e)}")
            raise

    def save_search_results(self, query, results):
        try:
            db_objects = []
            for result in results:
                db_result = SearchResultModel(
                    key_id=result.key_id,
                    query=query,
                    title=result.title,
                    content=result.content,
                    snippet=result.snippet,
                    link=result.link,
                    source=result.source
                )
                db_objects.append(db_result)

            self.session.add_all(db_objects)
            self.session.commit()
            logger.info(f"保存搜索结果成功，查询: {query}")
        except Exception as e:
            logger.error(f"保存搜索结果失败: {str(e)}")
            self.session.rollback()
            raise

    def close(self):
        if self.session:
            self.session.close()