from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from services.user_service import UserService
from services.tool_service import ToolService
from services.agent_model_config_service import AgentModelConfigService
from controllers import search_controller, user_controller, agent_controller, tool_controller, agent_model_config_controller
from controllers import agent_prompt_controller, invocation_controller, suggestion_controller, favorite_controller
from database.connection import Database
from dao.user_dao import UserDAO
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth_middleware import auth_middleware
from utils.logger import setup_logger
from config.settings import DATABASE_URL
from middleware.i18n_middleware import I18nMiddleware
from utils.i18n_utils import get_text
from utils.i18n_utils import load_translations
from services.agent_service import AgentService
from services.agent_model_config_service import AgentModelConfigService

logger = setup_logger('app')

# PostgreSQL 连接字符串
@asynccontextmanager
async def lifespan(app):
    # Startup code
    load_translations()
    # 初始化数据库
    db = Database(DATABASE_URL)
    db.init_database()
    
    # 初始化服务
    user_service = UserService(db)
    
    # 初始化新闻服务
    agent_service = AgentService(db)
    tool_service = ToolService(db)
    model_config_service = AgentModelConfigService(db)

    # 将服务实例存储到应用状态中
    app.state.user_service = user_service
    app.state.agent_service = agent_service
    app.state.tool_service = tool_service
    app.state.db = db
    
    # 初始化控制器
    user_controller.init_controller(user_service)
    agent_controller.init_controller(db)  # 初始化Agent控制器
    tool_controller.init_controller(tool_service)
    agent_model_config_controller.init_controller(model_config_service)
    agent_prompt_controller.init_controller(db)
    invocation_controller.init_controller(db)
    suggestion_controller.init_controller(db)  # 初始化建议控制器
    favorite_controller.init_controller(db)  # 初始化收藏控制器
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
app.include_router(agent_prompt_controller.router, prefix="/api")
app.include_router(search_controller.router, prefix="/api", tags=["搜索"])
app.include_router(user_controller.router, prefix="/api/users", tags=["用户"])
app.include_router(agent_controller.router, prefix="/api", tags=["Agent"])  # 注册Agent路由
app.include_router(tool_controller.router, prefix="/api/tools", tags=["工具"])
app.include_router(agent_model_config_controller.router, prefix="/api/model-configs", tags=["模型配置"])
app.include_router(invocation_controller.router, prefix="/api/invocations", tags=["Agent记录"])
app.include_router(suggestion_controller.router, prefix="/api", tags=["建议"])  # 注册建议路由
app.include_router(favorite_controller.router, prefix="/api", tags=["收藏"])  # 注册收藏路由

@app.get("/")
async def root():
    return {"message": "欢迎使用Info Card API"}




if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)