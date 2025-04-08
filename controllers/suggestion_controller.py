from fastapi import APIRouter, Depends, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from models.suggestion import SuggestionGenerateRequest
from dao.agent_dao import AgentDAO
from dao.suggestion_dao import SuggestionDAO
from utils.jwt_utils import decode_token 

logger = setup_logger('suggestion_controller')
router = APIRouter(tags=["建议"], include_in_schema=True)

# 全局变量存储DAO实例
agent_dao = None
suggestion_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_dao, suggestion_dao
    agent_dao = AgentDAO(db)
    suggestion_dao = SuggestionDAO(db)
    logger.info("建议控制器初始化完成")

@router.post("/suggestions/generate")
async def generate_suggestions(
    request_data: SuggestionGenerateRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """生成AI查询建议"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 获取语言设置
        lang = request.state.lang if hasattr(request.state, 'lang') else 'zh'
        
        # 从请求模型中获取参数
        query = request_data.query
        agent_id = request_data.agent_id
        
        # 如果没有提供agent_id，则查找name='建议agent'的agent
        if not agent_id:
            suggestion_agent = agent_dao.get_agent_by_name('建议agent')
            if not suggestion_agent:
                return error_response("未找到建议agent，请先创建", ErrorCode.NOT_FOUND)
            agent_id = suggestion_agent.key_id
        
        # 触发agent获取建议
        result = await agent_service.trigger_agent(
            agent_id=agent_id,
            user_id=current_user.user_id,
            lang=lang,
            query=query
        )
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"生成建议失败: {str(e)}")
        return error_response(f"生成建议失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/suggestions")
async def get_suggestions(
    request: Request
):
    """获取建议列表"""
    try:
      # 从请求头中获取token
        token = request.headers.get("Authorization")
        user_id = None
        
        # 如果有token，尝试解析
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
            try:
                # 解析token获取user_id
                payload = decode_token(token)
                if payload and "sub" in payload:
                    user_id = payload["sub"]
            except Exception as e:
                logger.warning(f"解析token失败: {str(e)}")
                user_id = "1ba06d2a-87b6-4baf-8945-43abe2731818"
        else:
            # 如果没有token，使用admin ID
            user_id = "1ba06d2a-87b6-4baf-8945-43abe2731818"

        
        logger.info(f"user_id: {user_id}")
        # 获取建议列表
        suggestions = await suggestion_dao.get_suggestions_by_agent(
            user_id=user_id,
            limit=5
        )
        
        # 格式化建议列表
        suggestion_list = []
        for suggestion in suggestions:
            suggestion_list.append(suggestion.content)
        
        # 返回结果
        return success_response(suggestion_list)
    except Exception as e:
        logger.error(f"获取建议列表失败: {str(e)}")
        return error_response(f"获取建议列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)