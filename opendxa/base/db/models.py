from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, Index, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BaseEntry(Base):
    """Base class for all storage entries."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class KnowledgeEntry(BaseEntry):
    """Model for knowledge entries."""
    __tablename__ = "knowledge"
    
    key = Column(String, nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    metadata = Column(JSON)
    
    __table_args__ = (
        Index('idx_knowledge_key', 'key'),
    )

class MemoryEntry(BaseEntry):
    """Model for memory entries."""
    __tablename__ = "memories"
    
    content = Column(JSON, nullable=False)
    context = Column(JSON)
    importance = Column(Float, default=1.0)
    decay_rate = Column(Float, default=0.1)
    last_accessed = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_memory_importance', 'importance'),
        Index('idx_memory_last_accessed', 'last_accessed'),
    ) 