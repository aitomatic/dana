"""Storage implementations for the OpenDXA system.

This module provides SQL and vector-based storage implementations for the OpenDXA system.
It includes the storage interfaces that handle the persistence of structured knowledge
and semantic memories.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Type
from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import numpy as np
from opendxa.common.db.base_model import BaseDBModel

M = TypeVar('M', bound=BaseDBModel)  # Model type

class BaseDBStorage(Generic[M], ABC):
    """Base interface for storage operations."""
    
    def __init__(self, db_model_class: Type[M]):
        """Initialize storage with model class.
        
        Args:
            db_model_class: The SQLAlchemy model class to use
        """
        self.db_model_class = db_model_class
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the storage system."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    @abstractmethod
    def store(self, key: str, content: Any, metadata: Optional[Dict] = None) -> None:
        """Store content with metadata."""
        pass
    
    @abstractmethod
    def retrieve(self, query: Optional[str] = None) -> List[Dict]:
        """Retrieve content."""
        pass
    
    @abstractmethod
    def delete(self, content_id: str) -> None:
        """Delete a value."""
        pass

class SqlDBStorage(BaseDBStorage[M], ABC):
    """SQL-based storage implementation for structured knowledge."""
    
    def __init__(self, connection_string: str, db_model_class: Type[M]):
        """Initialize SQL storage.
        
        Args:
            connection_string: Database connection string
            db_model_class: The SQLAlchemy model class to use
        """
        super().__init__(db_model_class)
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self._session: Optional[Session] = None
    
    def initialize(self) -> None:
        """Initialize the database tables."""
        self.db_model_class.metadata.create_all(self.engine)
        self._session = self.Session()
    
    def cleanup(self) -> None:
        """Clean up the database session."""
        if self._session:
            self._session.close()
    
    def store(self, key: str, content: Any, metadata: Optional[Dict] = None) -> None:
        """Store a knowledge entry in the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = self.db_model_class(
            key=key,
            value=content,
            metadata=metadata
        )
        self._session.add(entry)
        self._session.commit()
    
    def retrieve(self, query: Optional[str] = None) -> List[Dict]:
        """Retrieve a knowledge entry from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        if query:
            entry = self._session.query(self.db_model_class).filter_by(key=query).first()
        else:
            entry = self._session.query(self.db_model_class).first()
        return [entry.__dict__] if entry else []
    
    def delete(self, content_id: str) -> None:
        """Delete a knowledge entry from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = self._session.query(self.db_model_class).filter_by(key=content_id).first()
        if entry:
            self._session.delete(entry)
            self._session.commit()

class VectorDBStorage(BaseDBStorage[M], ABC):
    """Vector-based storage implementation for semantic memory."""
    
    def __init__(self, vector_db_url: str, embedding_model: Any, db_model_class: Type[M]):
        """Initialize vector storage.
        
        Args:
            vector_db_url: Vector database connection URL
            embedding_model: Model to generate embeddings
            db_model_class: The SQLAlchemy model class to use
        """
        super().__init__(db_model_class)
        self.vector_db_url = vector_db_url
        self.embedding_model = embedding_model
        self._session: Optional[Session] = None
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the vector database connection and schema."""
        # Initialize SQLAlchemy for metadata storage
        self.engine = create_engine(self.vector_db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.db_model_class.metadata.create_all(self.engine)
        self._session = self.Session()
    
    def cleanup(self) -> None:
        """Clean up vector database resources."""
        if self._session:
            self._session.close()
    
    def _generate_embedding(self, content: Any) -> np.ndarray:
        """Generate vector embedding for content."""
        # TODO: Implement embedding generation
        return np.zeros(768)  # Placeholder
    
    def store(self, key: str, content: Any, metadata: Optional[Dict] = None) -> None:
        """Store a memory with metadata."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        # Generate embedding for the content
        embedding = self._generate_embedding(content)
        
        # Add importance and decay rate to metadata if not present
        if metadata is None:
            metadata = {}
        if 'importance' not in metadata:
            metadata['importance'] = 1.0
        if 'decay_rate' not in metadata:
            metadata['decay_rate'] = 0.1
        
        # Store in vector DB
        entry = self.db_model_class(
            content=content,
            context=metadata,
            importance=metadata['importance'],
            decay_rate=metadata['decay_rate']
        )
        self._session.add(entry)
        self._session.commit()
        
        # TODO: Store embedding in vector DB
        # This is where we would store the embedding in a vector database
        # For now, we're just storing the metadata in SQL
    
    def retrieve(self, query: Optional[str] = None) -> List[Dict]:
        """Retrieve memories using vector similarity search."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        if not query:
            # If no query, return most important memories
            return self._retrieve_by_importance()
        
        # Generate embedding for query
        query_embedding = self._generate_embedding(query)
        
        # TODO: Search vector DB for similar memories
        # For now, we're just doing a simple content search
        entries = self._session.query(self.db_model_class).filter(
            self.db_model_class.content.ilike(f"%{query}%")
        ).order_by(self.db_model_class.importance.desc()).all()
        
        return [entry.__dict__ for entry in entries]
    
    def _retrieve_by_importance(self) -> List[Dict]:
        """Retrieve memories ordered by importance."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entries = self._session.query(self.db_model_class).order_by(
            self.db_model_class.importance.desc()
        ).all()
        return [entry.__dict__ for entry in entries]
    
    def delete(self, content_id: str) -> None:
        """Delete a memory from the database."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = self._session.query(self.db_model_class).filter_by(id=content_id).first()
        if entry:
            self._session.delete(entry)
            self._session.commit()
    
    def update_importance(self, memory_id: int, importance: float) -> None:
        """Update the importance of a memory."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entry = self._session.query(self.db_model_class).get(memory_id)
        if entry:
            entry.importance = importance
            self._session.commit()
    
    def decay_memories(self) -> None:
        """Apply decay to memories based on their decay rates."""
        if not self._session:
            raise RuntimeError("Storage not initialized")
        
        entries = self._session.query(self.db_model_class).all()
        for entry in entries:
            entry.importance *= (1 - entry.decay_rate)
        self._session.commit() 