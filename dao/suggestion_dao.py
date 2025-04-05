from database.suggestion import Suggestion
from utils.logger import setup_logger
import time

logger = setup_logger('suggestion_dao')

class SuggestionDAO:
    """推荐问题数据访问对象"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_suggestion(self, agent_id, content, user_id=None, context=None, language='zh'):
        """
        创建新的推荐问题
        
        Args:
            agent_id: Agent ID
            content: 推荐问题内容
            user_id: 用户ID (可选)
            context: 生成推荐的上下文 (可选)
            language: 问题语言 (默认中文)
            
        Returns:
            创建的推荐问题对象
        """
        try:
            session = self.db.get_session()
            try:
                suggestion = Suggestion(
                    agent_id=agent_id,
                    user_id=user_id,
                    content=content,
                    context=context,
                    language=language,
                    created_at=int(time.time())
                )
                session.add(suggestion)
                session.commit()
                return suggestion
            finally:
                session.close()
        except Exception as e:
            logger.error(f"创建推荐问题失败: {str(e)}")
            return None
    
    async def get_suggestions_by_agent(self, agent_id=None, user_id=None, language=None, limit=5):
        """
        获取指定Agent的推荐问题
        
        Args:
            agent_id: Agent ID (可选)
            user_id: 用户ID (可选)
            language: 问题语言 (可选)
            limit: 返回数量限制
            
        Returns:
            推荐问题列表
        """
        try:
            session = self.db.get_session()
            try:
                query = session.query(Suggestion)
                
                # 如果提供了agent_id，则进行过滤
                if agent_id:
                    query = query.filter(Suggestion.agent_id == agent_id)
                
                # 如果提供了user_id，则进行过滤
                if user_id:
                    query = query.filter(Suggestion.user_id == user_id)
                
                if language:
                    query = query.filter(Suggestion.language == language)
                
                # 按创建时间降序排序，获取最新的推荐
                suggestions = query.order_by(Suggestion.created_at.desc()).limit(limit).all()
                return suggestions
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取推荐问题失败: {str(e)}")
            return []
    
    
    async def get_suggestion_by_id(self, suggestion_id):
        """
        通过ID获取推荐问题
        
        Args:
            suggestion_id: 推荐问题ID
            
        Returns:
            推荐问题对象
        """
        try:
            session = self.db.get_session()
            try:
                suggestion = session.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
                return suggestion
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取推荐问题失败: {str(e)}")
            return None
    
    async def mark_suggestion_as_used(self, suggestion_id):
        """
        标记推荐问题为已使用
        
        Args:
            suggestion_id: 推荐问题ID
            
        Returns:
            是否成功
        """
        try:
            session = self.db.get_session()
            try:
                suggestion = session.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
                if suggestion:
                    suggestion.is_used = True
                    suggestion.updated_at = int(time.time())
                    session.commit()
                    return True
                return False
            finally:
                session.close()
        except Exception as e:
            logger.error(f"标记推荐问题为已使用失败: {str(e)}")
            return False
    
    async def delete_suggestion(self, suggestion_id):
        """
        删除推荐问题
        
        Args:
            suggestion_id: 推荐问题ID
            
        Returns:
            是否成功
        """
        try:
            session = self.db.get_session()
            try:
                suggestion = session.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
                if suggestion:
                    session.delete(suggestion)
                    session.commit()
                    return True
                return False
            finally:
                session.close()
        except Exception as e:
            logger.error(f"删除推荐问题失败: {str(e)}")
            return False
    
    async def delete_old_suggestions(self, days=30):
        """
        删除指定天数前的旧推荐问题
        
        Args:
            days: 天数
            
        Returns:
            删除的记录数
        """
        try:
            session = self.db.get_session()
            try:
                # 计算截止时间戳
                cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
                
                # 删除旧记录
                result = session.query(Suggestion).filter(Suggestion.created_at < cutoff_time).delete()
                session.commit()
                return result
            finally:
                session.close()
        except Exception as e:
            logger.error(f"删除旧推荐问题失败: {str(e)}")
            return 0