from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from services.search_service import SearchService
from services.user_service import UserService
from services.news_service import NewsService
from services.wired_news_service import WireNewsService
from services.bbc_news_service import BBCNewsService
from services.deepseek_service import DeepSeekService
from controllers import search_controller, user_controller, news_controller
from database.connection import Database
from dao.user_dao import UserDAO
from dao.search_dao import SearchDAO
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth_middleware import auth_middleware
from utils.logger import setup_logger
from config.settings import DATABASE_URL
from middleware.i18n_middleware import I18nMiddleware
from utils.i18n_utils import get_text
from controllers import news_controller
from utils.i18n_utils import load_translations

logger = setup_logger('app')

# PostgreSQL 连接字符串
@asynccontextmanager
async def lifespan(app):
    # Startup code
    load_translations()
    # 初始化数据库
    db = Database(DATABASE_URL)
    db.init_database()
    
    # 初始化DAO
    # user_dao = UserDAO(db)
    # search_dao = SearchDAO(db)
    
    # 初始化服务
    search_service = SearchService(db)
    user_service = UserService(db)
    
    # 初始化新闻服务
    wired_service = WireNewsService()
    bbc_service = BBCNewsService()
    chat_service = DeepSeekService()
    news_service = NewsService(wired_service, bbc_service, chat_service, db)
    
    # 将服务实例存储到应用状态中
    app.state.search_service = search_service
    app.state.user_service = user_service
    app.state.news_service = news_service
    
    # 初始化控制器
    search_controller.init_controller(search_service)
    user_controller.init_controller(user_service)
    news_controller.init_controller(news_service)
    
    logger.info("应用程序初始化完成")
    
    yield
    
    # 关闭数据库连接
    db.close()
    logger.info("关闭数据库连接")

app = FastAPI(title="Info Card API", lifespan=lifespan)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件
app.middleware("http")(auth_middleware)

# 添加国际化中间件
app.add_middleware(I18nMiddleware)

# 注册路由

# 在注册路由的部分添加
app.include_router(news_controller.router, prefix="/api")
app.include_router(search_controller.router, prefix="/api", tags=["搜索"])
app.include_router(user_controller.router, prefix="/api/users", tags=["用户"])

@app.get("/")
async def root():
    return {"message": "欢迎使用Info Card API"}

# Remove the old @app.on_event("startup") function
# @app.on_event("startup")
# async def startup_event():
#     # 加载翻译文件
#     load_translations()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)