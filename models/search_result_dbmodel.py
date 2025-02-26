from sqlalchemy import Column, Integer, String, Text, DateTime, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class SearchResultModel(Base):
    __tablename__ = 'search_results'

    id = Column(Integer, primary_key=True)
    key_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    query = Column(Text, nullable=False)
    title = Column(Text)
    content = Column(Text)
    snippet = Column(Text)
    link = Column(Text)
    source = Column(String(50))
    date = Column(DateTime(timezone=True), server_default=func.now())