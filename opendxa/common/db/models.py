"""Database models for the OpenDXA system.

This module contains SQLAlchemy models that define the database schema for the OpenDXA system.
It includes models for knowledge and memory storage, as well as the base model class.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BaseDBModel(Base):
    """Base model for all database entries."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
