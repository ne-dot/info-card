# 确保导入顺序正确
from .base import Base
# 先导入不依赖其他模型的基础模型
from .rss_feed import RSSFeed
from .rss_entry import RSSEntry
from .agent_rss_feed import AgentRSSFeed
# 然后导入其他模型
from .models import News, NewsSummary, NewsSummaryTrigger
from .user_models import UserModel, UserExternalAuth
from .agent import Agent
from .agent_model_config import AgentModelConfig
from .agent_prompt import AgentPrompt
# 确保所有模型都被注册
__all__ = [
    'Base',
    'RSSFeed',
    'RSSEntry',
    'AgentRSSFeed',
    'News', 
    'NewsSummary', 
    'NewsSummaryTrigger',
    'UserModel',
    'UserExternalAuth',
    'Agent',
    'AgentModelConfig',
    'AgentPrompt',
    'RSSFeed'
]