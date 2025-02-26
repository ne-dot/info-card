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