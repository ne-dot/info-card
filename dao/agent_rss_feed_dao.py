from database.agent_rss_feed import AgentRSSFeed
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from utils.logger import setup_logger

logger = setup_logger('agent_rss_feed_dao')

class AgentRSSFeedDao:
    """Agent与RSS源关联数据访问对象"""
    
    def __init__(self, db):
        """初始化DAO
        
        Args:
            db: 数据库会话工厂
        """
        self.db = db
    
    def create_agent_feed(self, agent_id, feed_id, priority=1, custom_filter=None):
        """创建Agent与RSS源的关联
        
        Args:
            agent_id: Agent ID
            feed_id: RSS源ID
            priority: 优先级
            custom_filter: 自定义过滤规则
            
        Returns:
            AgentRSSFeed: 创建的关联对象，失败返回None
        """
        try:
            with self.db.get_session() as session:
                # 检查是否已存在相同关联
                existing = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id,
                    AgentRSSFeed.feed_id == feed_id
                ).first()
                
                if existing:
                    logger.info(f"Agent与RSS源关联已存在: agent_id={agent_id}, feed_id={feed_id}")
                    return existing
                
                # 创建新关联
                agent_feed = AgentRSSFeed(
                    agent_id=agent_id,
                    feed_id=feed_id,
                    priority=priority,
                    custom_filter=custom_filter
                )
                session.add(agent_feed)
                session.commit()
                logger.info(f"创建Agent与RSS源关联成功: agent_id={agent_id}, feed_id={feed_id}")
                return agent_feed
        except SQLAlchemyError as e:
            logger.error(f"创建Agent与RSS源关联失败: {str(e)}")
            return None
    
    def get_agent_feed_by_id(self, agent_feed_id):
        """根据ID获取Agent与RSS源关联
        
        Args:
            agent_feed_id: 关联ID
            
        Returns:
            AgentRSSFeed: 关联对象，不存在返回None
        """
        try:
            with self.db.get_session() as session:
                return session.query(AgentRSSFeed).filter(AgentRSSFeed.id == agent_feed_id).first()
        except SQLAlchemyError as e:
            logger.error(f"获取Agent与RSS源关联失败: {str(e)}")
            return None
    
    def get_agent_feed(self, agent_id, feed_id):
        """根据Agent ID和RSS源ID获取关联
        
        Args:
            agent_id: Agent ID
            feed_id: RSS源ID
            
        Returns:
            AgentRSSFeed: 关联对象，不存在返回None
        """
        try:
            with self.db.get_session() as session:
                return session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id,
                    AgentRSSFeed.feed_id == feed_id
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"获取Agent与RSS源关联失败: {str(e)}")
            return None
    
    def get_feeds_by_agent(self, agent_id):
        """获取指定Agent关联的所有RSS源
        
        Args:
            agent_id: Agent ID
            
        Returns:
            list: AgentRSSFeed对象列表
        """
        try:
            with self.db.get_session() as session:
                return session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id
                ).order_by(AgentRSSFeed.priority.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"获取Agent关联的RSS源失败: {str(e)}")
            return []
    
    def get_agents_by_feed(self, feed_id):
        """获取关联指定RSS源的所有Agent
        
        Args:
            feed_id: RSS源ID
            
        Returns:
            list: AgentRSSFeed对象列表
        """
        try:
            with self.db.get_session() as session:
                return session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.feed_id == feed_id
                ).order_by(AgentRSSFeed.priority.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"获取关联RSS源的Agent失败: {str(e)}")
            return []
    
    def update_agent_feed(self, agent_feed_id, **kwargs):
        """更新Agent与RSS源关联信息
        
        Args:
            agent_feed_id: 关联ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db.get_session() as session:
                agent_feed = session.query(AgentRSSFeed).filter(AgentRSSFeed.id == agent_feed_id).first()
                if not agent_feed:
                    logger.warning(f"更新失败，Agent与RSS源关联不存在: {agent_feed_id}")
                    return False
                
                # 更新提供的字段
                for key, value in kwargs.items():
                    if hasattr(agent_feed, key):
                        setattr(agent_feed, key, value)
                
                session.commit()
                logger.info(f"更新Agent与RSS源关联成功: {agent_feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新Agent与RSS源关联失败: {str(e)}")
            return False
    
    def update_priority(self, agent_id, feed_id, priority):
        """更新关联的优先级
        
        Args:
            agent_id: Agent ID
            feed_id: RSS源ID
            priority: 新的优先级
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db.get_session() as session:
                agent_feed = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id,
                    AgentRSSFeed.feed_id == feed_id
                ).first()
                
                if not agent_feed:
                    logger.warning(f"更新优先级失败，关联不存在: agent_id={agent_id}, feed_id={feed_id}")
                    return False
                
                agent_feed.priority = priority
                session.commit()
                logger.info(f"更新关联优先级成功: agent_id={agent_id}, feed_id={feed_id}, priority={priority}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新关联优先级失败: {str(e)}")
            return False
    
    def update_custom_filter(self, agent_id, feed_id, custom_filter):
        """更新关联的自定义过滤规则
        
        Args:
            agent_id: Agent ID
            feed_id: RSS源ID
            custom_filter: 新的过滤规则
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db.get_session() as session:
                agent_feed = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id,
                    AgentRSSFeed.feed_id == feed_id
                ).first()
                
                if not agent_feed:
                    logger.warning(f"更新过滤规则失败，关联不存在: agent_id={agent_id}, feed_id={feed_id}")
                    return False
                
                agent_feed.custom_filter = custom_filter
                session.commit()
                logger.info(f"更新关联过滤规则成功: agent_id={agent_id}, feed_id={feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新关联过滤规则失败: {str(e)}")
            return False
    
    def delete_agent_feed(self, agent_feed_id):
        """删除Agent与RSS源关联
        
        Args:
            agent_feed_id: 关联ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            with self.db.get_session() as session:
                agent_feed = session.query(AgentRSSFeed).filter(AgentRSSFeed.id == agent_feed_id).first()
                if not agent_feed:
                    logger.warning(f"删除失败，Agent与RSS源关联不存在: {agent_feed_id}")
                    return False
                
                session.delete(agent_feed)
                session.commit()
                logger.info(f"删除Agent与RSS源关联成功: {agent_feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"删除Agent与RSS源关联失败: {str(e)}")
            return False
    
    def delete_agent_feed_by_ids(self, agent_id, feed_id):
        """根据Agent ID和RSS源ID删除关联
        
        Args:
            agent_id: Agent ID
            feed_id: RSS源ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            with self.db.get_session() as session:
                agent_feed = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id,
                    AgentRSSFeed.feed_id == feed_id
                ).first()
                
                if not agent_feed:
                    logger.warning(f"删除失败，关联不存在: agent_id={agent_id}, feed_id={feed_id}")
                    return False
                
                session.delete(agent_feed)
                session.commit()
                logger.info(f"删除关联成功: agent_id={agent_id}, feed_id={feed_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"删除关联失败: {str(e)}")
            return False
    
    def delete_feeds_by_agent(self, agent_id):
        """删除指定Agent的所有RSS源关联
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: 删除的关联数量
        """
        try:
            with self.db.get_session() as session:
                count = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.agent_id == agent_id
                ).delete()
                
                session.commit()
                logger.info(f"删除Agent的所有RSS源关联成功: agent_id={agent_id}, count={count}")
                return count
        except SQLAlchemyError as e:
            logger.error(f"删除Agent的所有RSS源关联失败: {str(e)}")
            return 0
    
    def delete_agents_by_feed(self, feed_id):
        """删除指定RSS源的所有Agent关联
        
        Args:
            feed_id: RSS源ID
            
        Returns:
            int: 删除的关联数量
        """
        try:
            with self.db.get_session() as session:
                count = session.query(AgentRSSFeed).filter(
                    AgentRSSFeed.feed_id == feed_id
                ).delete()
                
                session.commit()
                logger.info(f"删除RSS源的所有Agent关联成功: feed_id={feed_id}, count={count}")
                return count
        except SQLAlchemyError as e:
            logger.error(f"删除RSS源的所有Agent关联失败: {str(e)}")
            return 0