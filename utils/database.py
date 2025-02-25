import psycopg2
from psycopg2.extras import DictCursor
from utils.logger import setup_logger

logger = setup_logger('database')

class Database:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise

    def init_database(self):
        try:
            with self.conn.cursor() as cur:
                # 创建 UUID 扩展（如果不存在）
                cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
                
                # 创建搜索结果表
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS search_results (
                        id SERIAL,
                        key_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                        query TEXT NOT NULL,
                        title TEXT,
                        content TEXT,
                        snippet TEXT,
                        link TEXT,
                        source TEXT,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
                logger.info("数据表初始化成功")
        except Exception as e:
            logger.error(f"数据表初始化失败: {str(e)}")
            raise

    def save_search_results(self, query, results):
        try:
            with self.conn.cursor() as cur:
                for result in results:
                    cur.execute("""
                        INSERT INTO search_results 
                        (query, title, content, snippet, link, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        query,
                        result.title,
                        result.content,
                        result.snippet,
                        result.link,
                        result.source
                    ))
                self.conn.commit()
                logger.info(f"保存搜索结果成功，查询: {query}")
        except Exception as e:
            logger.error(f"保存搜索结果失败: {str(e)}")
            self.conn.rollback()
            raise

    def close(self):
        if self.conn:
            self.conn.close()