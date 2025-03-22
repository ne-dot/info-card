from database.agent_model_config import AgentModelConfig
from utils.logger import setup_logger
import json

logger = setup_logger('agent_model_config_dao')

class AgentModelConfigDAO:
    def __init__(self, db):
        self.db = db
        
    async def create_model_config(self, model_name, weight=1.0, priority=1, 
                                 is_enabled=True, config=None, base_api_url=None, api_key=None):
        """创建模型配置"""
        try:
            session = self.db.get_session()
            
            # 如果config是字典，转换为JSON字符串
            if isinstance(config, dict):
                config = json.dumps(config)
                
            model_config = AgentModelConfig(
                model_name=model_name,
                weight=weight,
                priority=priority,
                is_enabled=is_enabled,
                config=config,
                base_api_url=base_api_url,
                api_key=api_key
            )
            
            session.add(model_config)
            session.commit()
            session.refresh(model_config)
            
            # 转换为字典
            model_config_dict = self._convert_to_dict(model_config)
            
            logger.info(f"创建模型配置成功: {model_name}")
            return model_config_dict
        except Exception as e:
            session.rollback()
            logger.error(f"创建模型配置失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    async def get_model_config_by_id(self, config_id):
        """根据ID获取模型配置"""
        try:
            session = self.db.get_session()
            model_config = session.query(AgentModelConfig).filter(AgentModelConfig.id == config_id).first()
            
            if not model_config:
                return None
                
            # 转换为字典
            model_config_dict = self._convert_to_dict(model_config)
            
            return model_config_dict
        except Exception as e:
            logger.error(f"获取模型配置失败: {str(e)}")
            return None
        finally:
            session.close()
            
            
    async def update_model_config(self, config_id, **kwargs):
        """更新模型配置"""
        try:
            session = self.db.get_session()
            model_config = session.query(AgentModelConfig).filter(AgentModelConfig.id == config_id).first()
            
            if not model_config:
                logger.warning(f"模型配置不存在: {config_id}")
                return None
                
            # 处理config字段，如果是字典则转换为JSON字符串
            if 'config' in kwargs and isinstance(kwargs['config'], dict):
                kwargs['config'] = json.dumps(kwargs['config'])
                
            # 更新属性
            for key, value in kwargs.items():
                if hasattr(model_config, key):
                    setattr(model_config, key, value)
                    
            session.commit()
            session.refresh(model_config)
            
            # 转换为字典
            model_config_dict = self._convert_to_dict(model_config)
            
            logger.info(f"更新模型配置成功: {config_id}")
            return model_config_dict
        except Exception as e:
            session.rollback()
            logger.error(f"更新模型配置失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    async def delete_model_config(self, config_id):
        """删除模型配置"""
        try:
            session = self.db.get_session()
            model_config = session.query(AgentModelConfig).filter(AgentModelConfig.id == config_id).first()
            
            if not model_config:
                logger.warning(f"模型配置不存在: {config_id}")
                return False
                
            session.delete(model_config)
            session.commit()
            
            logger.info(f"删除模型配置成功: {config_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"删除模型配置失败: {str(e)}")
            raise e
        finally:
            session.close()
            
    async def get_all_model_configs(self, page=1, page_size=10):
        """获取所有模型配置"""
        try:
            session = self.db.get_session()
            
            # 计算总数
            total = session.query(AgentModelConfig).count()
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询分页数据
            model_configs = session.query(AgentModelConfig).order_by(
                AgentModelConfig.model_name
            ).offset(offset).limit(page_size).all()
            
            # 转换为字典列表
            model_configs_dict = [self._convert_to_dict(config) for config in model_configs]
            
            return model_configs_dict, total
        except Exception as e:
            logger.error(f"获取所有模型配置失败: {str(e)}")
            return [], 0
        finally:
            session.close()
            
    def _convert_to_dict(self, model_config):
        """将模型配置对象转换为字典"""
        if not model_config:
            return None
            
        # 尝试解析config字段为JSON
        config = model_config.config
        if config:
            try:
                config = json.loads(config)
            except:
                pass
            
        # 创建基本字典
        result = {
            "id": model_config.id,
            "model_name": model_config.model_name,
            "weight": model_config.weight,
            "priority": model_config.priority,
            "is_enabled": model_config.is_enabled,
            "config": config,
            "base_api_url": model_config.base_api_url,
            "api_key": model_config.api_key
        }
                
        return result