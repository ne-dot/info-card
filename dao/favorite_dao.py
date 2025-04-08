from database.favorite_models import FavoriteModel
from models.favorite import Favorite
from sqlalchemy import select
import uuid
import time
import json
from utils.logger import setup_logger

logger = setup_logger('favorite_dao')

class FavoriteDAO:
    def __init__(self, db):
        self.db = db
    
    async def create_favorite(self, user_id: str, source_type: str, title: str = None, 
                            content: str = None, url: str = None, image_url: str = None, tag_id: str = None):
        """创建收藏记录"""
        try:
            session = self.db.get_session()
            try:
                # 创建收藏模型
                now = int(time.time())
                favorite_model = FavoriteModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    source_type=source_type,
                    title=title,
                    content=content,
                    url=url,
                    image_url=image_url,
                    tag_id=tag_id,
                    created_at=now,
                    updated_at=now
                )
                
                # 添加到数据库
                session.add(favorite_model)
                session.commit()
                
                # 转换为业务模型
                return Favorite(
                    id=favorite_model.id,
                    user_id=favorite_model.user_id,
                    source_type=favorite_model.source_type,
                    title=favorite_model.title,
                    content=favorite_model.content,
                    url=favorite_model.url,
                    image_url=favorite_model.image_url,
                    tag_id=favorite_model.tag_id,
                    created_at=favorite_model.created_at,
                    updated_at=favorite_model.updated_at,
                    is_deleted=favorite_model.is_deleted
                )
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"创建收藏失败: {str(e)}")
            return None
    
    async def get_favorites_by_user(self, user_id: str, source_type: str = None, 
                                   limit: int = 10, offset: int = 0):
        """获取用户的收藏列表"""
        try:
            session = self.db.get_session()
            try:
                # 构建查询
                query = session.query(FavoriteModel).filter(
                    FavoriteModel.user_id == user_id,
                    FavoriteModel.is_deleted == False
                )
                
                # 如果指定了来源类型，添加过滤条件
                if source_type:
                    query = query.filter(FavoriteModel.source_type == source_type)
                
                # 按创建时间倒序排序，分页
                query = query.order_by(FavoriteModel.created_at.desc())
                query = query.offset(offset).limit(limit)
                
                # 执行查询
                favorite_models = query.all()
                
                # 转换为业务模型
                favorites = []
                for model in favorite_models:
                    favorites.append(Favorite(
                        id=model.id,
                        user_id=model.user_id,
                        source_type=model.source_type,
                        title=model.title,
                        content=model.content,
                        url=model.url,
                        image_url=model.image_url,
                        tag_id=model.tag_id,
                        created_at=model.created_at,
                        updated_at=model.updated_at,
                        is_deleted=model.is_deleted
                    ))
                
                return favorites
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取收藏列表失败: {str(e)}")
            return []
    
    async def get_favorite_by_id(self, favorite_id: str):
        """通过ID获取收藏记录"""
        try:
            session = self.db.get_session()
            try:
                favorite_model = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                if favorite_model:
                    return Favorite(
                        id=favorite_model.id,
                        user_id=favorite_model.user_id,
                        source_type=favorite_model.source_type,
                        title=favorite_model.title,
                        content=favorite_model.content,
                        url=favorite_model.url,
                        image_url=favorite_model.image_url,
                        tag_id=favorite_model.tag_id,
                        created_at=favorite_model.created_at,
                        updated_at=favorite_model.updated_at,
                        is_deleted=favorite_model.is_deleted
                    )
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取收藏记录失败: {str(e)}")
            return None
    
    async def update_favorite(self, favorite_id: str, title: str = None, 
                            content: str = None, url: str = None, image_url: str = None, tag_id: str = None):
        """更新收藏记录"""
        try:
            session = self.db.get_session()
            try:
                favorite_model = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                if favorite_model:
                    # 更新字段
                    if title is not None:
                        favorite_model.title = title
                    if content is not None:
                        favorite_model.content = content
                    if url is not None:
                        favorite_model.url = url
                    if image_url is not None:
                        favorite_model.image_url = image_url
                    if tag_id is not None:
                        favorite_model.tag_id = tag_id
                    
                    # 更新时间戳
                    favorite_model.updated_at = int(time.time())
                    
                    # 提交更改
                    session.commit()
                    
                    # 返回更新后的模型
                    return Favorite(
                        id=favorite_model.id,
                        user_id=favorite_model.user_id,
                        source_type=favorite_model.source_type,
                        title=favorite_model.title,
                        content=favorite_model.content,
                        url=favorite_model.url,
                        image_url=favorite_model.image_url,
                        tag_id=favorite_model.tag_id,
                        created_at=favorite_model.created_at,
                        updated_at=favorite_model.updated_at,
                        is_deleted=favorite_model.is_deleted
                    )
                return None
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新收藏记录失败: {str(e)}")
            return None
    
    async def delete_favorite(self, favorite_id: str):
        """软删除收藏记录"""
        try:
            session = self.db.get_session()
            try:
                favorite_model = session.query(FavoriteModel).filter(
                    FavoriteModel.id == favorite_id,
                    FavoriteModel.is_deleted == False
                ).first()
                
                if favorite_model:
                    # 软删除
                    favorite_model.is_deleted = True
                    favorite_model.updated_at = int(time.time())
                    
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
            logger.error(f"删除收藏记录失败: {str(e)}")
            return False 