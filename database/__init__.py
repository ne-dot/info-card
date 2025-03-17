from .base import Base
from .models import News, NewsSummary, NewsSummaryTrigger
from .user_models import UserModel, UserExternalAuth
from .agent import Agent
from .agent_model_config import AgentModelConfig
from .agent_prompt import AgentPrompt
from .rss_feed import RSSFeed
# Import other models as needed

# This ensures all models are registered with SQLAlchemy
__all__ = [
    'Base', 
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