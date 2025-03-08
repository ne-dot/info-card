from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from services.chat_service import ChatService
from services.auth_service import AuthService
from controllers import search_controller, user_controller
from database.connection import Database
from dao.user_dao import UserDAO
from dao.search_dao import SearchDAO
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth_middleware import auth_middleware
from utils.logger import setup_logger
from config.settings import DATABASE_URL
from middleware.i18n_middleware import I18nMiddleware
from utils.i18n_utils import get_text

logger = setup_logger('app')

# PostgreSQL 连接字符串
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    db = Database(DATABASE_URL)
    db.init_database()
    
    # 初始化DAO
    # user_dao = UserDAO(db)
    # search_dao = SearchDAO(db)
    
    # 初始化服务
    chat_service = ChatService(db)
    auth_service = AuthService(db)
    
    # 初始化控制器
    search_controller.init_controller(chat_service)
    user_controller.init_controller(auth_service)
    
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
app.include_router(search_controller.router, prefix="/api", tags=["搜索"])
app.include_router(user_controller.router, prefix="/api/users", tags=["用户"])

@app.get("/")
async def root():
    return {"message": "欢迎使用Info Card API"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)