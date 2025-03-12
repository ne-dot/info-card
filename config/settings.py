import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 应用配置
APP_NAME = "智能搜索助手"
APP_HOST = "0.0.0.0"
APP_PORT = 8000

# API 密钥
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://neondb_owner:npg_wgixrLkJB31N@ep-wandering-dawn-a8c402vl-pooler.eastus2.azure.neon.tech/neondb?sslmode=require")


"""
应用程序配置设置
"""

# 新闻服务配置
NEWS_SETTINGS = {
    # RSS源URL
    "rss_urls": {
        "wired": "https://www.wired.com/feed/",
        "bbc": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "bbc_football": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "espc_soccer": "https://www.espn.com/espn/rss/soccer/news"
    },
    
    # 默认获取的新闻数量
    "default_news_limit": 10,
    
    # 最大新闻数量限制
    "max_news_limit": 50
}