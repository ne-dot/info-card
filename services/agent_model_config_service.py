from dao.agent_model_config_dao import AgentModelConfigDAO
from utils.logger import setup_logger
from utils.response_utils import ErrorCode

logger = setup_logger('agent_model_config_service')

class AgentModelConfigService:
    def __init__(self, db):
        self.db = db
        self.model_config_dao = AgentModelConfigDAO(db)
        
    async def create_model_config(self, model_name, weight=1.0, priority=1, 
                                 is_enabled=True, config=None, base_api_url=None, api_key=None):
        """创建模型配置"""
        try:
            model_config = await self.model_config_dao.create_model_config(
                model_name=model_name,
                weight=weight,
                priority=priority,
                is_enabled=is_enabled,
                config=config,
                base_api_url=base_api_url,
                api_key=api_key
            )
            return model_config, None, None
        except Exception as e:
            logger.error(f"创建模型配置服务失败: {str(e)}")
            return None, f"创建模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def get_model_config(self, config_id):
        """获取模型配置详情"""
        try:
            model_config = await self.model_config_dao.get_model_config_by_id(config_id)
            if not model_config:
                return None, "模型配置不存在", ErrorCode.RESOURCE_NOT_FOUND
            return model_config, None, None
        except Exception as e:
            logger.error(f"获取模型配置服务失败: {str(e)}")
            return None, f"获取模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def get_all_model_configs(self, page=1, page_size=10):
        """获取所有模型配置"""
        try:
            model_configs, total = await self.model_config_dao.get_all_model_configs(page, page_size)
            return model_configs, total, None, None
        except Exception as e:
            logger.error(f"获取所有模型配置服务失败: {str(e)}")
            return None, 0, f"获取所有模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def update_model_config(self, config_id, **kwargs):
        """更新模型配置"""
        try:
            model_config = await self.model_config_dao.update_model_config(config_id, **kwargs)
            if not model_config:
                return None, "模型配置不存在", ErrorCode.RESOURCE_NOT_FOUND
            return model_config, None, None
        except Exception as e:
            logger.error(f"更新模型配置服务失败: {str(e)}")
            return None, f"更新模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR
            
    async def delete_model_config(self, config_id):
        """删除模型配置"""
        try:
            result = await self.model_config_dao.delete_model_config(config_id)
            if not result:
                return False, "模型配置不存在", ErrorCode.RESOURCE_NOT_FOUND
            return True, None, None
        except Exception as e:
            logger.error(f"删除模型配置服务失败: {str(e)}")
            return False, f"删除模型配置失败: {str(e)}", ErrorCode.UNKNOWN_ERROR