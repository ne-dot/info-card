# 导入所有数据库模型
from .base import Base
from .agent import Agent
from .agent_invocation import AgentInvocation
from .ai_summary import AISummary
# 修正导入路径
from .search_raw_data import SearchRawData  # 假设文件名是 search_raw_data.py
from .rss_feed import RSSFeed
from .rss_entry import RSSEntry
from .agent_rss_feed import AgentRSSFeed
from .user_models import UserModel, UserExternalAuth
from .agent_model_config import AgentModelConfig
from .agent_prompt import AgentPrompt
# 添加导入
from .suggestion import Suggestion
from .tag_models import TagModel
from .favorite_models import FavoriteModel

# 确保所有模型都被注册
__all__ = [
    'Base',
    'RSSFeed',
    'RSSEntry',
    'AgentRSSFeed',
    'UserModel',
    'UserExternalAuth',
    'Agent',
    'AgentModelConfig',
    'AgentPrompt',
    'AgentInvocation',
    'AISummary',
    'SearchRawData',
    'TagModel',
    'FavoriteModel',
    'Suggestion'
]