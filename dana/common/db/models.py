"""Database models for the Dana system.

This module contains SQLAlchemy models that define the specific database schema
for memory and knowledge storage.

It includes models for knowledge and short-term, long-term, and permanent memory models along
with their respective table names.
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, Index, String

from dana.common.db.base_model import BaseDBModel


class KnowledgeDBModel(BaseDBModel):
    """Model for structured knowledge storage."""

    __tablename__ = "knowledge_base"

    key = Column(String, nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    knowledge_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("idx_knowledge_key", "key"),)


class MemoryDBModel(BaseDBModel):
    """Base model for memory storage."""

    __abstract__ = True

    content = Column(String, nullable=False)
    context = Column(JSON, nullable=True)
    importance = Column(Float, default=1.0)
    decay_rate = Column(Float, default=0.1)
    last_accessed = Column(DateTime, default=lambda: datetime.now(UTC))


class STMemoryDBModel(MemoryDBModel):
    """Model for short-term memory storage."""

    __tablename__ = "st_memory"

    decay_rate = Column(Float, default=0.2)

    __table_args__ = (Index("idx_st_memory_importance", "importance"),)


class LTMemoryDBModel(MemoryDBModel):
    """Model for long-term memory storage."""

    __tablename__ = "lt_memory"

    decay_rate = Column(Float, default=0.01)

    __table_args__ = (Index("idx_lt_memory_importance", "importance"),)


class PermanentMemoryDBModel(MemoryDBModel):
    """Model for permanent memory storage."""

    __tablename__ = "perm_memory"

    decay_rate = Column(Float, default=0.0)

    __table_args__ = (Index("idx_perm_memory_importance", "importance"),)
