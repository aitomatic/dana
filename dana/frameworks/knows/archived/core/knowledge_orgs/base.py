"""Base classes for Knowledge Organizations."""

from enum import Enum
from typing import Any, Protocol, TypeVar

T = TypeVar('T')

class KnowledgeOrganization(Protocol):
    """Base protocol for knowledge organizations."""
    
    def store(self, key: str, value: Any) -> None:
        """Store a value in the organization."""
        ...
    
    def retrieve(self, key: str) -> Any | None:
        """Retrieve a value from the organization."""
        ...
    
    def delete(self, key: str) -> None:
        """Delete a value from the organization."""
        ...
    
    def query(self, **kwargs) -> list[Any]:
        """Query values from the organization."""
        ...

class KnowledgeType(Enum):
    """Types of knowledge organizations."""
    SEMI_STRUCTURED = "semi_structured"
    VECTOR = "vector"
    TIME_SERIES = "time_series"
    RELATIONAL = "relational"

class KnowledgeError(Exception):
    """Base exception for knowledge organization errors."""
    pass

class StorageError(KnowledgeError):
    """Error during storage operations."""
    pass

class RetrievalError(KnowledgeError):
    """Error during retrieval operations."""
    pass

class QueryError(KnowledgeError):
    """Error during query operations."""
    pass

class ValidationError(KnowledgeError):
    """Error during validation operations."""
    pass 