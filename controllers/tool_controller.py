from fastapi import APIRouter, Depends, HTTPException, status
from models.tool import ToolCreate, ToolUpdate, ToolResponse, ToolType
from services.tool_service import ToolService
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response
from dependencies.auth import get_current_user
from typing import List, Dict

router = APIRouter()
logger = setup_logger('tool_controller')
tool_service = None

def init_controller(service: ToolService):
    global tool_service
    tool_service = service

# 修改获取工具类型的接口
@router.get("/types", response_model=Dict[str, str])
async def get_tool_types():
    """获取所有可用的工具类型"""
    try:
        tool_types, error, error_code = await tool_service.get_tool_types()
        
        if error:
            return error_response(error, error_code)
            
        return success_response(tool_types, "获取工具类型成功")
    except Exception as e:
        logger.error(f"获取工具类型失败: {str(e)}")
        return error_response(f"获取工具类型失败: {str(e)}")

@router.post("/", response_model=ToolResponse)
async def create_tool(tool_data: ToolCreate, current_user = Depends(get_current_user)):
    """创建新工具"""
    try:
        tool_dict, error, error_code = await tool_service.create_tool(
            name=tool_data.name,
            tool_type=tool_data.tool_type,
            endpoint=tool_data.endpoint,
            description=tool_data.description,
            config_params=tool_data.config_params
        )
        
        if error:
            return error_response(error, error_code)
        
        # 打印返回的字典，用于调试
        logger.debug(f"服务层返回的工具字典: {tool_dict}")
            
        return success_response(tool_dict, "创建工具成功")
    except Exception as e:
        logger.error(f"创建工具失败: {str(e)}")
        return error_response(f"创建工具失败: {str(e)}")

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, current_user = Depends(get_current_user)):
    """获取工具详情"""
    try:
        tool, error, error_code = await tool_service.get_tool(tool_id)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(tool, "获取工具成功")
    except Exception as e:
        logger.error(f"获取工具失败: {str(e)}")
        return error_response(f"获取工具失败: {str(e)}")

@router.get("", response_model=List[ToolResponse])
async def get_all_tools(
    current_user = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10
):
    """获取所有工具，支持分页
    
    Args:
        page: 页码，从1开始
        page_size: 每页数量
    """
    try:
        tools, total, error, error_code = await tool_service.get_all_tools(page, page_size)
        
        if error:
            return error_response(error, error_code)
        
        # 构建包含分页信息的响应
        response_data = {
            "items": tools,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
            
        return success_response(response_data, "获取所有工具成功")
    except Exception as e:
        logger.error(f"获取所有工具失败: {str(e)}")
        return error_response(f"获取所有工具失败: {str(e)}")

@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, tool_data: ToolUpdate, current_user = Depends(get_current_user)):
    """更新工具信息"""
    try:
        # 将非None的字段转换为字典
        update_data = {k: v for k, v in tool_data.dict().items() if v is not None}
        
        tool, error, error_code = await tool_service.update_tool(tool_id, **update_data)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(tool, "更新工具成功")
    except Exception as e:
        logger.error(f"更新工具失败: {str(e)}")
        return error_response(f"更新工具失败: {str(e)}")

@router.delete("/{tool_id}")
async def delete_tool(tool_id: str, current_user = Depends(get_current_user)):
    """删除工具"""
    try:
        result, error, error_code = await tool_service.delete_tool(tool_id)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(None, "删除工具成功")
    except Exception as e:
        logger.error(f"删除工具失败: {str(e)}")
        return error_response(f"删除工具失败: {str(e)}")