"""Dana integration for knowledge organizations."""

from typing import Any

from dana.frameworks.knows.core.knowledge_orgs.base import KnowledgeOrganization, QueryError, RetrievalError, StorageError
from dana.frameworks.knows.core.knowledge_orgs.config import RedisSettings, RelationalSettings, TimeSeriesSettings, VectorStoreSettings
from dana.frameworks.knows.core.knowledge_orgs.relational import RelationalStore
from dana.frameworks.knows.core.knowledge_orgs.semi_structured import SemiStructuredStore
from dana.frameworks.knows.core.knowledge_orgs.time_series import TimeSeriesStore
from dana.frameworks.knows.core.knowledge_orgs.vector import VectorStore

# Global store registry
_stores: dict[str, KnowledgeOrganization] = {}

class KnowledgeStoreTypes:
    """Knowledge store type constants for Dana integration."""
    SEMI_STRUCTURED = "semi_structured"
    VECTOR = "vector"
    TIME_SERIES = "time_series"
    RELATIONAL = "relational"

def create_store(store_type: str, settings: dict[str, Any]) -> None:
    """Create a knowledge store instance.
    
    Args:
        store_type: Type of store to create
        settings: Store configuration settings
        
    Raises:
        StorageError: If store creation fails
    """
    try:
        if store_type == KnowledgeStoreTypes.SEMI_STRUCTURED:
            config = RedisSettings(**settings)
            store = SemiStructuredStore(config)
        elif store_type == KnowledgeStoreTypes.VECTOR:
            config = VectorStoreSettings(**settings)
            store = VectorStore(config)
        elif store_type == KnowledgeStoreTypes.TIME_SERIES:
            config = TimeSeriesSettings(**settings)
            store = TimeSeriesStore(config)
        elif store_type == KnowledgeStoreTypes.RELATIONAL:
            config = RelationalSettings(**settings)
            store = RelationalStore(config)
        else:
            raise ValueError(f"Unknown store type: {store_type}")
        
        _stores[store_type] = store
    except Exception as e:
        raise StorageError(f"Failed to create store: {e}")

def store_value(key: str, value: Any, store_type: str) -> None:
    """Store a value in the appropriate store.
    
    Args:
        key: Key to store under
        value: Value to store
        store_type: Type of store to use
        
    Raises:
        StorageError: If storage fails
    """
    try:
        store = _stores.get(store_type)
        if store is None:
            raise ValueError(f"No store found for type: {store_type}")
        
        store.store(key, value)
    except Exception as e:
        raise StorageError(f"Failed to store value: {e}")

def retrieve_value(key: str, store_type: str) -> Any | None:
    """Retrieve a value from the appropriate store.
    
    Args:
        key: Key to retrieve
        store_type: Type of store to use
        
    Returns:
        Retrieved value or None if not found
        
    Raises:
        RetrievalError: If retrieval fails
    """
    try:
        store = _stores.get(store_type)
        if store is None:
            raise ValueError(f"No store found for type: {store_type}")
        
        return store.retrieve(key)
    except Exception as e:
        raise RetrievalError(f"Failed to retrieve value: {e}")

def delete_value(key: str, store_type: str) -> None:
    """Delete a value from the appropriate store.
    
    Args:
        key: Key to delete
        store_type: Type of store to use
        
    Raises:
        StorageError: If deletion fails
    """
    try:
        store = _stores.get(store_type)
        if store is None:
            raise ValueError(f"No store found for type: {store_type}")
        
        store.delete(key)
    except Exception as e:
        raise StorageError(f"Failed to delete value: {e}")

def query_values(store_type: str, **kwargs) -> list[Any]:
    """Query values from the appropriate store.
    
    Args:
        store_type: Type of store to use
        **kwargs: Query parameters
        
    Returns:
        List of matching values
        
    Raises:
        QueryError: If query fails
    """
    try:
        store = _stores.get(store_type)
        if store is None:
            raise ValueError(f"No store found for type: {store_type}")
        
        return store.query(**kwargs)
    except Exception as e:
        raise QueryError(f"Failed to query values: {e}")

def close_stores() -> None:
    """Close all store connections."""
    for store in _stores.values():
        try:
            if hasattr(store, 'close'):
                store.close()
        except Exception:
            pass
    _stores.clear()

def get_store_types() -> dict[str, str]:
    """Get available store types.
    
    Returns:
        Dictionary of store type constants
    """
    return {
        "SEMI_STRUCTURED": KnowledgeStoreTypes.SEMI_STRUCTURED,
        "VECTOR": KnowledgeStoreTypes.VECTOR,
        "TIME_SERIES": KnowledgeStoreTypes.TIME_SERIES,
        "RELATIONAL": KnowledgeStoreTypes.RELATIONAL
    }

def get_active_stores() -> list[str]:
    """Get list of active store types.
    
    Returns:
        List of active store type names
    """
    return list(_stores.keys())

# Type conversion utilities for Dana integration
def convert_dana_to_python(value: Any) -> Any:
    """Convert Dana values to Python equivalents.
    
    Args:
        value: Dana value to convert
        
    Returns:
        Python equivalent value
    """
    # Handle Dana-specific types here
    if isinstance(value, dict):
        return {k: convert_dana_to_python(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_dana_to_python(v) for v in value]
    else:
        return value

def convert_python_to_dana(value: Any) -> Any:
    """Convert Python values to Dana equivalents.
    
    Args:
        value: Python value to convert
        
    Returns:
        Dana equivalent value
    """
    # Handle Python-specific types here
    if isinstance(value, dict):
        return {k: convert_python_to_dana(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_python_to_dana(v) for v in value]
    else:
        return value 