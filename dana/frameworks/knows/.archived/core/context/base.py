"""Base context classes and types for the KNOWS framework."""

from datetime import datetime
from enum import Enum
from typing import Any


class ContextType(Enum):
    """Types of context in the system."""
    ENVIRONMENTAL = "environmental"
    AGENT = "agent"
    WORKFLOW = "workflow"


class ContextError(Exception):
    """Base exception for context-related errors."""
    pass


class ContextSyncError(ContextError):
    """Exception raised when context synchronization fails."""
    pass


class ContextValidationError(ContextError):
    """Exception raised when context validation fails."""
    pass


class Context:
    """Base context class for managing contextual data."""
    
    def __init__(self, context_type: ContextType):
        """Initialize a new context.
        
        Args:
            context_type: The type of context to create
        """
        self.type: ContextType = context_type
        self.data: dict[str, Any] = {}
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
    
    def set(self, key: str, value: Any) -> None:
        """Set a context value.
        
        Args:
            key: The key to set
            value: The value to store
            
        Raises:
            ContextValidationError: If key is invalid
        """
        if not isinstance(key, str) or not key.strip():
            raise ContextValidationError("Key must be a non-empty string")
        
        self.data[key] = value
        self.updated_at = datetime.now()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value.
        
        Args:
            key: The key to retrieve
            default: Default value if key not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        return self.data.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the context.
        
        Args:
            key: The key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self.data
    
    def remove(self, key: str) -> bool:
        """Remove a key from the context.
        
        Args:
            key: The key to remove
            
        Returns:
            True if key was removed, False if key didn't exist
        """
        if key in self.data:
            del self.data[key]
            self.updated_at = datetime.now()
            return True
        return False
    
    def clear(self) -> None:
        """Clear all context data."""
        self.data.clear()
        self.updated_at = datetime.now()
    
    def keys(self) -> list[str]:
        """Get all keys in the context.
        
        Returns:
            List of all keys in the context
        """
        return list(self.data.keys())
    
    def values(self) -> list[Any]:
        """Get all values in the context.
        
        Returns:
            List of all values in the context
        """
        return list(self.data.values())
    
    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs in the context.
        
        Returns:
            List of (key, value) tuples
        """
        return list(self.data.items())
    
    def size(self) -> int:
        """Get the number of items in the context.
        
        Returns:
            Number of key-value pairs in the context
        """
        return len(self.data)
    
    def copy(self) -> "Context":
        """Create a copy of this context.
        
        Returns:
            A new Context instance with the same data
        """
        new_context = Context(self.type)
        new_context.data = self.data.copy()
        new_context.created_at = self.created_at
        new_context.updated_at = self.updated_at
        return new_context
    
    def merge(self, other: "Context") -> None:
        """Merge another context into this one.
        
        Args:
            other: The context to merge from
            
        Raises:
            ContextValidationError: If contexts are incompatible
        """
        if not isinstance(other, Context):
            raise ContextValidationError("Can only merge with another Context instance")
        
        self.data.update(other.data)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary representation.
        
        Returns:
            Dictionary representation of the context
        """
        return {
            "type": self.type.value,
            "data": self.data.copy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Context":
        """Create a context from dictionary representation.
        
        Args:
            data: Dictionary representation of context
            
        Returns:
            New Context instance
            
        Raises:
            ContextValidationError: If data is invalid
        """
        try:
            context_type = ContextType(data["type"])
            context = cls(context_type)
            context.data = data["data"].copy()
            context.created_at = datetime.fromisoformat(data["created_at"])
            context.updated_at = datetime.fromisoformat(data["updated_at"])
            return context
        except (KeyError, ValueError, TypeError) as e:
            raise ContextValidationError(f"Invalid context data: {e}")
    
    def __str__(self) -> str:
        """String representation of the context."""
        return f"Context(type={self.type.value}, size={self.size()}, updated={self.updated_at})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the context."""
        return (f"Context(type={self.type.value}, data={self.data}, "
                f"created_at={self.created_at}, updated_at={self.updated_at})")
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another context."""
        if not isinstance(other, Context):
            return False
        return (self.type == other.type and 
                self.data == other.data and
                self.created_at == other.created_at and
                self.updated_at == other.updated_at) 