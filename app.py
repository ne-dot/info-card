from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from services.chat_service import ChatService
from controllers.search_controller import router as search_router, init_controller
from utils.database import Database
from config.settings import DATABASE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    db = Database(DATABASE_URL)
    db.init_database()
    
    # 初始化服务
    chat_service = ChatService(db)
    
    # 初始化控制器
    init_controller(chat_service)
    
    yield
    
    # 关闭数据库连接
    db.close()

app = FastAPI(title="搜索服务 API", lifespan=lifespan)

# 注册路由
app.include_router(search_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
