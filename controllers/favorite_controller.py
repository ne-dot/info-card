from fastapi import APIRouter, Depends, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from models.favorite import FavoriteCreate, FavoriteUpdate, FavoriteResponse
from dao.favorite_dao import FavoriteDAO

logger = setup_logger('favorite_controller')
router = APIRouter(tags=["收藏"], include_in_schema=True)

# 全局变量存储DAO实例
favorite_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global favorite_dao
    favorite_dao = FavoriteDAO(db)
    logger.info("收藏控制器初始化完成")

@router.post("/favorites", response_model=FavoriteResponse)
async def create_favorite(
    favorite_data: FavoriteCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建收藏记录"""
    try:
        # 创建收藏记录
        favorite = await favorite_dao.create_favorite(
            user_id=current_user.user_id,
            source_type=favorite_data.source_type,
            title=favorite_data.title,
            content=favorite_data.content,
            url=favorite_data.url,
            image_url=favorite_data.image_url,
            tag_id=favorite_data.tag_id
        )
        
        if not favorite:
            return error_response("创建收藏失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(favorite.dict())
    except Exception as e:
        logger.error(f"创建收藏失败: {str(e)}")
        return error_response(f"创建收藏失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/favorites", response_model=list[FavoriteResponse])
async def get_favorites(
    source_type: str = None,
    limit: int = 10,
    offset: int = 0,
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户的收藏列表"""
    try:
        # 获取收藏列表
        favorites = await favorite_dao.get_favorites_by_user(
            user_id=current_user.user_id,
            source_type=source_type,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应模型
        favorite_list = [favorite.dict() for favorite in favorites]
        
        return success_response(favorite_list)
    except Exception as e:
        logger.error(f"获取收藏列表失败: {str(e)}")
        return error_response(f"获取收藏列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/favorites/{favorite_id}", response_model=FavoriteResponse)
async def get_favorite(
    favorite_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取收藏记录详情"""
    try:
        # 获取收藏记录
        favorite = await favorite_dao.get_favorite_by_id(favorite_id)
        
        if not favorite:
            return error_response("收藏记录不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if favorite.user_id != current_user.user_id:
            return error_response("无权访问此收藏记录", ErrorCode.PERMISSION_DENIED)
        
        return success_response(favorite.dict())
    except Exception as e:
        logger.error(f"获取收藏记录失败: {str(e)}")
        return error_response(f"获取收藏记录失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.put("/favorites/{favorite_id}", response_model=FavoriteResponse)
async def update_favorite(
    favorite_id: str,
    favorite_data: FavoriteUpdate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新收藏记录"""
    try:
        # 获取收藏记录
        favorite = await favorite_dao.get_favorite_by_id(favorite_id)
        
        if not favorite:
            return error_response("收藏记录不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if favorite.user_id != current_user.user_id:
            return error_response("无权修改此收藏记录", ErrorCode.PERMISSION_DENIED)
        
        # 更新收藏记录
        updated_favorite = await favorite_dao.update_favorite(
            favorite_id=favorite_id,
            title=favorite_data.title,
            content=favorite_data.content,
            url=favorite_data.url,
            image_url=favorite_data.image_url,
            tag_id=favorite_data.tag_id
        )
        
        if not updated_favorite:
            return error_response("更新收藏记录失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(updated_favorite.dict())
    except Exception as e:
        logger.error(f"更新收藏记录失败: {str(e)}")
        return error_response(f"更新收藏记录失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.delete("/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除收藏记录"""
    try:
        # 获取收藏记录
        favorite = await favorite_dao.get_favorite_by_id(favorite_id)
        
        if not favorite:
            return error_response("收藏记录不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if favorite.user_id != current_user.user_id:
            return error_response("无权删除此收藏记录", ErrorCode.PERMISSION_DENIED)
        
        # 删除收藏记录
        success = await favorite_dao.delete_favorite(favorite_id)
        
        if not success:
            return error_response("删除收藏记录失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(None, "删除收藏记录成功")
    except Exception as e:
        logger.error(f"删除收藏记录失败: {str(e)}")
        return error_response(f"删除收藏记录失败: {str(e)}", ErrorCode.UNKNOWN_ERROR) 