from fastapi import APIRouter, Depends, HTTPException, status
from models.agent_model_config import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse
from services.agent_model_config_service import AgentModelConfigService
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response
from dependencies.auth import get_current_user
from typing import List, Dict

router = APIRouter()
logger = setup_logger('agent_model_config_controller')
model_config_service = None

def init_controller(service: AgentModelConfigService):
    global model_config_service
    model_config_service = service

@router.post("/", response_model=ModelConfigResponse)
async def create_model_config(model_config_data: ModelConfigCreate, current_user = Depends(get_current_user)):
    """创建新的模型配置"""
    try:
        model_config, error, error_code = await model_config_service.create_model_config(
            model_name=model_config_data.model_name,
            weight=model_config_data.weight,
            priority=model_config_data.priority,
            is_enabled=model_config_data.is_enabled,
            config=model_config_data.config,
            base_api_url=model_config_data.base_api_url,
            api_key=model_config_data.api_key
        )
        
        if error:
            return error_response(error, error_code)
            
        return success_response(model_config, "创建模型配置成功")
    except Exception as e:
        logger.error(f"创建模型配置失败: {str(e)}")
        return error_response(f"创建模型配置失败: {str(e)}")

@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(config_id: str, current_user = Depends(get_current_user)):
    """获取模型配置详情"""
    try:
        model_config, error, error_code = await model_config_service.get_model_config(config_id)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(model_config, "获取模型配置成功")
    except Exception as e:
        logger.error(f"获取模型配置失败: {str(e)}")
        return error_response(f"获取模型配置失败: {str(e)}")

@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(config_id: str, model_config_data: ModelConfigUpdate, current_user = Depends(get_current_user)):
    """更新模型配置"""
    try:
        # 将非None的字段转换为字典
        update_data = {k: v for k, v in model_config_data.dict().items() if v is not None}
        
        model_config, error, error_code = await model_config_service.update_model_config(config_id, **update_data)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(model_config, "更新模型配置成功")
    except Exception as e:
        logger.error(f"更新模型配置失败: {str(e)}")
        return error_response(f"更新模型配置失败: {str(e)}")

@router.delete("/{config_id}")
async def delete_model_config(config_id: str, current_user = Depends(get_current_user)):
    """删除模型配置"""
    try:
        result, error, error_code = await model_config_service.delete_model_config(config_id)
        
        if error:
            return error_response(error, error_code)
            
        return success_response(None, "删除模型配置成功")
    except Exception as e:
        logger.error(f"删除模型配置失败: {str(e)}")
        return error_response(f"删除模型配置失败: {str(e)}")

@router.get("/", response_model=Dict)
async def get_all_model_configs(
    page: int = 1, 
    page_size: int = 10,
    current_user = Depends(get_current_user)
):
    """获取所有模型配置"""
    try:
        model_configs, total, error, error_code = await model_config_service.get_all_model_configs(
            page, page_size
        )
        
        if error:
            return error_response(error, error_code)
        
        # 构建包含分页信息的响应
        response_data = {
            "items": model_configs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
            
        return success_response(response_data, "获取所有模型配置成功")
    except Exception as e:
        logger.error(f"获取所有模型配置失败: {str(e)}")
        return error_response(f"获取所有模型配置失败: {str(e)}")