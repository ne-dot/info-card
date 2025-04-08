from database.tag_models import TagModel
from models.tag import Tag
from sqlalchemy import select
import uuid
import time
from utils.logger import setup_logger

logger = setup_logger('tag_dao')

class TagDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_tag(self, user_id: str, name: str, description: str = None):
        """创建标签"""
        try:
            session = self.db.get_session()
            try:
                # 检查标签是否已存在
                existing_tag = session.query(TagModel).filter(
                    TagModel.user_id == user_id,
                    TagModel.name == name,
                    TagModel.is_deleted == False
                ).first()
                
                if existing_tag:
                    return Tag(
                        id=existing_tag.id,
                        user_id=existing_tag.user_id,
                        name=existing_tag.name,
                        description=existing_tag.description,
                        created_at=existing_tag.created_at,
                        updated_at=existing_tag.updated_at,
                        is_deleted=existing_tag.is_deleted
                    )
                
                # 创建标签模型
                now = int(time.time())
                tag_model = TagModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    name=name,
                    description=description,
                    created_at=now,
                    updated_at=now
                )
                
                # 添加到数据库
                session.add(tag_model)
                session.commit()
                
                # 转换为业务模型
                return Tag(
                    id=tag_model.id,
                    user_id=tag_model.user_id,
                    name=tag_model.name,
                    description=tag_model.description,
                    created_at=tag_model.created_at,
                    updated_at=tag_model.updated_at,
                    is_deleted=tag_model.is_deleted
                )
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"创建标签失败: {str(e)}")
            return None
    
    async def get_tags(self, user_id: str = None, limit: int = 100, offset: int = 0):
        """获取标签列表"""
        try:
            session = self.db.get_session()
            try:
                # 构建查询
                query = session.query(TagModel).filter(
                    TagModel.is_deleted == False
                )
                
                # 如果指定了用户ID，添加过滤条件
                if user_id:
                    query = query.filter(TagModel.user_id == user_id)
                
                # 按名称排序，分页
                query = query.order_by(TagModel.name)
                query = query.offset(offset).limit(limit)
                
                # 执行查询
                tag_models = query.all()
                
                # 转换为业务模型
                tags = []
                for model in tag_models:
                    tags.append(Tag(
                        id=model.id,
                        user_id=model.user_id,
                        name=model.name,
                        description=model.description,
                        created_at=model.created_at,
                        updated_at=model.updated_at,
                        is_deleted=model.is_deleted
                    ))
                
                return tags
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取标签列表失败: {str(e)}")
            return []
    
    async def get_tag_by_id(self, tag_id: str):
        """通过ID获取标签"""
        try:
            session = self.db.get_session()
            try:
                tag_model = session.query(TagModel).filter(
                    TagModel.id == tag_id,
                    TagModel.is_deleted == False
                ).first()
                
                if tag_model:
                    return Tag(
                        id=tag_model.id,
                        user_id=tag_model.user_id,
                        name=tag_model.name,
                        description=tag_model.description,
                        created_at=tag_model.created_at,
                        updated_at=tag_model.updated_at,
                        is_deleted=tag_model.is_deleted
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取标签失败: {str(e)}")
            return None
    
    async def get_tag_by_name(self, user_id: str, name: str):
        """通过名称获取标签"""
        try:
            session = self.db.get_session()
            try:
                tag_model = session.query(TagModel).filter(
                    TagModel.user_id == user_id,
                    TagModel.name == name,
                    TagModel.is_deleted == False
                ).first()
                
                if tag_model:
                    return Tag(
                        id=tag_model.id,
                        user_id=tag_model.user_id,
                        name=tag_model.name,
                        description=tag_model.description,
                        created_at=tag_model.created_at,
                        updated_at=tag_model.updated_at,
                        is_deleted=tag_model.is_deleted
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取标签失败: {str(e)}")
            return None
    
    async def update_tag(self, tag_id: str, name: str = None, description: str = None):
        """更新标签"""
        try:
            session = self.db.get_session()
            try:
                tag_model = session.query(TagModel).filter(
                    TagModel.id == tag_id,
                    TagModel.is_deleted == False
                ).first()
                
                if tag_model:
                    # 更新字段
                    if name is not None:
                        tag_model.name = name
                    if description is not None:
                        tag_model.description = description
                    
                    # 更新时间戳
                    tag_model.updated_at = int(time.time())
                    
                    # 提交更改
                    session.commit()
                    
                    # 返回更新后的模型
                    return Tag(
                        id=tag_model.id,
                        user_id=tag_model.user_id,
                        name=tag_model.name,
                        description=tag_model.description,
                        created_at=tag_model.created_at,
                        updated_at=tag_model.updated_at,
                        is_deleted=tag_model.is_deleted
                    )
                return None
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新标签失败: {str(e)}")
            return None
    
    async def delete_tag(self, tag_id: str):
        """软删除标签"""
        try:
            session = self.db.get_session()
            try:
                tag_model = session.query(TagModel).filter(
                    TagModel.id == tag_id,
                    TagModel.is_deleted == False
                ).first()
                
                if tag_model:
                    # 软删除
                    tag_model.is_deleted = True
                    tag_model.updated_at = int(time.time())
                    
                    # 提交更改
                    session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"删除标签失败: {str(e)}")
            return False
    
    async def add_tag_to_favorite(self, favorite_id: str, tag_id: str):
        """为收藏添加标签"""
        try:
            session = self.db.get_session()
            try:
                # 获取收藏和标签
                favorite = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                tag = session.query(TagModel).filter(
                    TagModel.id == tag_id,
                    TagModel.is_deleted == False
                ).first()
                
                if favorite and tag:
                    # 检查是否已关联
                    if tag not in favorite.tags:
                        favorite.tags.append(tag)
                        session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"为收藏添加标签失败: {str(e)}")
            return False
    
    async def remove_tag_from_favorite(self, favorite_id: str, tag_id: str):
        """从收藏中移除标签"""
        try:
            session = self.db.get_session()
            try:
                # 获取收藏和标签
                favorite = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                tag = session.query(TagModel).filter(
                    TagModel.id == tag_id,
                    TagModel.is_deleted == False
                ).first()
                
                if favorite and tag:
                    # 检查是否已关联
                    if tag in favorite.tags:
                        favorite.tags.remove(tag)
                        session.commit()
                    return True
                return False
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"从收藏中移除标签失败: {str(e)}")
            return False
    
    async def get_favorite_tags(self, favorite_id: str):
        """获取收藏的标签列表"""
        try:
            session = self.db.get_session()
            try:
                # 获取收藏
                favorite = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                if favorite:
                    # 转换为业务模型
                    tags = []
                    for tag_model in favorite.tags:
                        tags.append(Tag(
                            id=tag_model.id,
                            user_id=tag_model.user_id,
                            name=tag_model.name,
                            description=tag_model.description,
                            created_at=tag_model.created_at,
                            updated_at=tag_model.updated_at,
                            is_deleted=tag_model.is_deleted
                        ))
                    return tags
                return []
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取收藏标签列表失败: {str(e)}")
            return [] 