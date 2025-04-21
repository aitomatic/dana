from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from opendxa.base.db.models import KnowledgeEntry, MemoryEntry
from abc import ABC, abstractmethod

Base = declarative_base()

class BaseStorage(ABC):
    """Base interface for storage operations."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the storage system."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    @abstractmethod
    def store(self, content: Any, metadata: Optional[Dict] = None) -> None:
        """Store a value."""
        pass
    
    @abstractmethod
    def retrieve(self, query: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """Retrieve a value."""
        pass
    
    @abstractmethod
    def delete(self, content_id: str) -> None:
        """Delete a value."""
        pass

class MemoryStorage(BaseStorage):
    """Interface for memory storage operations."""
    
    @abstractmethod
    def store(
        self,
        content: Any,
        metadata: Optional[Dict] = None,
        importance: float = 1.0,
        decay_rate: float = 0.1
    ) -> None:
        """Store a memory entry."""
        pass
    
    @abstractmethod
    def retrieve(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve memory entries."""
        pass
    
    @abstractmethod
    def update_importance(self, memory_id: int, importance: float) -> None:
        """Update the importance of a memory."""
        pass
    
    @abstractmethod
    def decay_memories(self) -> None:
        """Apply decay to memories based on their decay rates."""
        pass

class SQLMemoryStorage(MemoryStorage):
    """SQL-based implementation of memory storage."""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self._session: Optional[Session] = None
    
    def initialize(self) -> None:
        """Initialize the database tables."""
        Base.metadata.create_all(self.engine)
        self._session = self.Session()
    
    def cleanup(self) -> None:
        """Clean up the database session."""
        if self._session:
            self._session.close()
    
    def store(
        self,
        content: Any,
        metadata: Optional[Dict] = None,
        importance: float = 1.0,
        decay_rate: float = 0.1
    ) -> None:
        """Store a memory entry in the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        memory = MemoryEntry(
            content=content,
            metadata=metadata or {},
            importance=importance,
            decay_rate=decay_rate,
            created_at=datetime.utcnow()
        )
        self._session.add(memory)
        self._session.commit()
    
    def retrieve(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve memory entries from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        query_builder = self._session.query(MemoryEntry)
        if query:
            query_builder = query_builder.filter(MemoryEntry.content.ilike(f"%{query}%"))
        
        memories = query_builder.order_by(MemoryEntry.importance.desc()).limit(limit).all()
        return [memory.to_dict() for memory in memories]
    
    def update_importance(self, memory_id: int, importance: float) -> None:
        """Update the importance of a memory in the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        memory = self._session.query(MemoryEntry).get(memory_id)
        if memory:
            memory.importance = importance
            self._session.commit()
    
    def decay_memories(self) -> None:
        """Apply decay to memories based on their decay rates."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        memories = self._session.query(MemoryEntry).all()
        for memory in memories:
            memory.importance *= (1 - memory.decay_rate)
        self._session.commit()

class KnowledgeStorage(BaseStorage):
    """Interface for knowledge storage operations."""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self._session: Optional[Session] = None
    
    def initialize(self) -> None:
        """Initialize the database tables."""
        Base.metadata.create_all(self.engine)
        self._session = self.Session()
    
    def cleanup(self) -> None:
        """Clean up the database session."""
        if self._session:
            self._session.close()
    
    def store(self, content: Any, metadata: Optional[Dict] = None) -> None:
        """Store a knowledge entry in the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = KnowledgeEntry(
            content=content,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        self._session.add(entry)
        self._session.commit()
    
    def retrieve(self, query: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """Retrieve a knowledge entry from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        if query:
            entry = self._session.query(KnowledgeEntry).filter_by(content=query).first()
        else:
            entry = self._session.query(KnowledgeEntry).first()
        return entry.content if entry else None
    
    def delete(self, content_id: str) -> None:
        """Delete a knowledge entry from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = self._session.query(KnowledgeEntry).filter_by(id=content_id).first()
        if entry:
            self._session.delete(entry)
            self._session.commit() 