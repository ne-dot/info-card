from typing import Dict, Any, Optional
from utils.logger import setup_logger

logger = setup_logger('model_factory')

class ModelFactory:
    """模型工厂类，用于创建不同类型的AI模型服务"""
    
    @staticmethod
    def create_model_service(model_name: str, model_params: Optional[Dict[str, Any]] = None):
        """
        根据模型名称创建对应的模型服务实例
        
        Args:
            model_name: 模型名称
            model_params: 模型参数
            
        Returns:
            模型服务实例
        
        Raises:
            Exception: 如果不支持该模型类型
        """
        model_name_lower = model_name.lower()
        
        # DeepSeek模型
        if "deepseek" in model_name_lower:
            from services.deepseek_service import DeepSeekService
            logger.info(f"创建DeepSeek模型服务: {model_name}")
            return DeepSeekService()
        
        # ChatGPT模型
        elif "gpt" in model_name_lower:
            from services.chatgpt_service import ChatGPTService
            logger.info(f"创建ChatGPT模型服务: {model_name}")
            return ChatGPTService()
        
        # 百度文心一言模型
        elif "ernie" in model_name_lower or "wenxin" in model_name_lower:
            from services.ernie_service import ErnieService
            logger.info(f"创建文心一言模型服务: {model_name}")
            return ErnieService()
        
        # 智谱AI模型
        elif "chatglm" in model_name_lower or "zhipu" in model_name_lower:
            from services.zhipu_service import ZhipuService
            logger.info(f"创建智谱AI模型服务: {model_name}")
            return ZhipuService()
        
        # 可以继续添加其他模型类型
        
        # 不支持的模型类型
        else:
            logger.error(f"不支持的模型类型: {model_name}")
            raise Exception(f"不支持的模型类型: {model_name}")