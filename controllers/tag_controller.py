from fastapi import APIRouter, Depends, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from models.tag import TagCreate, TagUpdate, TagResponse, TagListResponse
from dao.tag_dao import TagDAO

logger = setup_logger('tag_controller')
router = APIRouter(tags=["标签"], include_in_schema=True)

# 全局变量存储DAO实例
tag_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global tag_dao
    tag_dao = TagDAO(db)
    logger.info("标签控制器初始化完成")

@router.post("/tags", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建标签"""
    try:
        # 使用当前用户ID
        user_id = current_user["id"]
        
        # 创建标签
        tag = await tag_dao.create_tag(
            user_id=user_id,
            name=tag_data.name,
            description=tag_data.description
        )
        
        if not tag:
            return error_response("创建标签失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(tag.dict())
    except Exception as e:
        logger.error(f"创建标签失败: {str(e)}")
        return error_response(f"创建标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/tags", response_model=TagListResponse)
async def get_tags(
    user_id: str = None,
    limit: int = 100,
    offset: int = 0,
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取标签列表"""
    try:
        # 如果未指定用户ID，使用当前用户ID
        if not user_id:
            user_id = current_user["id"]
        
        # 获取标签列表
        tags = await tag_dao.get_tags(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应模型
        tag_list = [tag.dict() for tag in tags]
        
        return success_response({
            "tags": tag_list,
            "total": len(tag_list)
        })
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        return error_response(f"获取标签列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取标签详情"""
    try:
        # 获取标签
        tag = await tag_dao.get_tag_by_id(tag_id)
        
        if not tag:
            return error_response("标签不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if tag.user_id != current_user["id"]:
            return error_response("无权限访问此标签", ErrorCode.UNAUTHORIZED)
        
        return success_response(tag.dict())
    except Exception as e:
        logger.error(f"获取标签失败: {str(e)}")
        return error_response(f"获取标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新标签"""
    try:
        # 获取标签
        tag = await tag_dao.get_tag_by_id(tag_id)
        
        if not tag:
            return error_response("标签不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if tag.user_id != current_user["id"]:
            return error_response("无权限修改此标签", ErrorCode.UNAUTHORIZED)
        
        # 更新标签
        updated_tag = await tag_dao.update_tag(
            tag_id=tag_id,
            name=tag_data.name,
            description=tag_data.description
        )
        
        if not updated_tag:
            return error_response("更新标签失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(updated_tag.dict())
    except Exception as e:
        logger.error(f"更新标签失败: {str(e)}")
        return error_response(f"更新标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.delete("/tags/{tag_id}", response_model=TagResponse)
async def delete_tag(
    tag_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除标签"""
    try:
        # 获取标签
        tag = await tag_dao.get_tag_by_id(tag_id)
        
        if not tag:
            return error_response("标签不存在", ErrorCode.NOT_FOUND)
        
        # 检查权限
        if tag.user_id != current_user["id"]:
            return error_response("无权限删除此标签", ErrorCode.UNAUTHORIZED)
        
        # 删除标签
        success = await tag_dao.delete_tag(tag_id)
        
        if not success:
            return error_response("删除标签失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(None, "标签已删除")
    except Exception as e:
        logger.error(f"删除标签失败: {str(e)}")
        return error_response(f"删除标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.post("/favorites/{favorite_id}/tags/{tag_id}")
async def add_tag_to_favorite(
    favorite_id: str,
    tag_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """为收藏添加标签"""
    try:
        # 为收藏添加标签
        success = await tag_dao.add_tag_to_favorite(favorite_id, tag_id)
        
        if not success:
            return error_response("为收藏添加标签失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(None, "为收藏添加标签成功")
    except Exception as e:
        logger.error(f"为收藏添加标签失败: {str(e)}")
        return error_response(f"为收藏添加标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.delete("/favorites/{favorite_id}/tags/{tag_id}")
async def remove_tag_from_favorite(
    favorite_id: str,
    tag_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """从收藏中移除标签"""
    try:
        # 从收藏中移除标签
        success = await tag_dao.remove_tag_from_favorite(favorite_id, tag_id)
        
        if not success:
            return error_response("从收藏中移除标签失败", ErrorCode.UNKNOWN_ERROR)
        
        return success_response(None, "从收藏中移除标签成功")
    except Exception as e:
        logger.error(f"从收藏中移除标签失败: {str(e)}")
        return error_response(f"从收藏中移除标签失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/favorites/{favorite_id}/tags", response_model=TagListResponse)
async def get_favorite_tags(
    favorite_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取收藏的标签列表"""
    try:
        # 获取收藏的标签列表
        tags = await tag_dao.get_favorite_tags(favorite_id)
        
        # 转换为响应模型
        tag_list = [tag.dict() for tag in tags]
        
        return success_response({
            "tags": tag_list,
            "total": len(tag_list)
        })
    except Exception as e:
        logger.error(f"获取收藏标签列表失败: {str(e)}")
        return error_response(f"获取收藏标签列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR) 