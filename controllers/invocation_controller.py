from fastapi import APIRouter, Depends, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from services.invocation_service import InvocationService

logger = setup_logger('invocation_controller')
router = APIRouter(tags=["Invocation"], include_in_schema=True)

# 全局变量存储服务实例
invocation_service = None

def init_controller(db):
    """初始化控制器，设置全局服务实例"""
    global invocation_service
    invocation_service = InvocationService(db)
    logger.info("Invocation控制器初始化完成")

@router.get("")
async def get_all_invocations(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
    agent_id: str = None,
    status: str = None
):
    """获取所有调用记录列表
    
    Args:
        request: Request对象
        current_user: 当前用户
        page: 页码，默认为1
        page_size: 每页数量，默认为10
        agent_id: 根据Agent ID过滤，可选
        status: 根据状态过滤，可选值: pending, processing, success, failed
        
    Returns:
        所有调用记录列表和分页信息
    """
    try:
        # 调用服务获取所有调用记录列表，传入过滤参数
        result = await invocation_service.get_all_invocations(
            page, page_size, current_user.user_id, agent_id, status
        )
        
        return success_response(result)
    except Exception as e:
        logger.error(f"获取所有调用记录列表失败: {str(e)}")
        return error_response(f"获取所有调用记录列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/{invocation_id}")
async def get_invocation_detail(
    invocation_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取调用记录详情
    
    Args:
        invocation_id: 调用记录ID
        
    Returns:
        调用记录详情
    """
    try:
        # 调用服务获取调用记录详情
        result = await invocation_service.get_invocation_detail(
            invocation_id, current_user.user_id
        )
        
        return success_response(result)
    except Exception as e:
        logger.error(f"获取调用记录详情失败: {str(e)}")
        return error_response(f"获取调用记录详情失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)
