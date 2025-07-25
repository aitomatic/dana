"""Dana language integration for context management."""

from typing import Any

from dana.frameworks.knows.core.context.base import ContextType
from dana.frameworks.knows.core.context.config import ContextSettings
from dana.frameworks.knows.core.context.manager import ContextManager

# Global context manager instance
_context_manager: ContextManager | None = None


def _get_context_manager() -> ContextManager:
    """Get or create the global context manager instance.
    
    Returns:
        The global context manager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def _parse_context_type(context_type_str: str) -> ContextType:
    """Parse context type string to ContextType enum.
    
    Args:
        context_type_str: String representation of context type
        
    Returns:
        ContextType enum value
        
    Raises:
        ValueError: If context type is invalid
    """
    context_type_str = context_type_str.lower().strip()
    
    type_mapping = {
        "environmental": ContextType.ENVIRONMENTAL,
        "env": ContextType.ENVIRONMENTAL,
        "environment": ContextType.ENVIRONMENTAL,
        "agent": ContextType.AGENT,
        "workflow": ContextType.WORKFLOW,
        "wf": ContextType.WORKFLOW
    }
    
    if context_type_str not in type_mapping:
        valid_types = list(type_mapping.keys())
        raise ValueError(f"Invalid context type '{context_type_str}'. Valid types: {valid_types}")
    
    return type_mapping[context_type_str]


# Dana-callable functions for context management

def context_set(context_type: str, key: str, value: Any) -> bool:
    """Set a value in the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        key: The key to set
        value: The value to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        manager.set_context_value(ctx_type, key, value)
        return True
    except Exception:
        return False


def context_get(context_type: str, key: str, default: Any = None) -> Any:
    """Get a value from the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        key: The key to retrieve
        default: Default value if key not found
        
    Returns:
        The value associated with the key, or default if not found
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        return manager.get_context_value(ctx_type, key, default)
    except Exception:
        return default


def context_has(context_type: str, key: str) -> bool:
    """Check if a key exists in the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        key: The key to check
        
    Returns:
        True if key exists, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        return manager.has_context_value(ctx_type, key)
    except Exception:
        return False


def context_remove(context_type: str, key: str) -> bool:
    """Remove a key from the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        key: The key to remove
        
    Returns:
        True if key was removed, False if key didn't exist or error occurred
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        return manager.remove_context_value(ctx_type, key)
    except Exception:
        return False


def context_clear(context_type: str) -> bool:
    """Clear all data in the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        manager.clear_context(ctx_type)
        return True
    except Exception:
        return False


def context_clear_all() -> bool:
    """Clear all contexts.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        manager.clear_all_contexts()
        return True
    except Exception:
        return False


def context_sync(source_type: str, target_type: str, keys: list[str] | None = None) -> bool:
    """Synchronize data between contexts.
    
    Args:
        source_type: Source context type ("environmental", "agent", "workflow")
        target_type: Target context type ("environmental", "agent", "workflow")
        keys: Optional list of specific keys to sync (sync all if None)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        source_ctx_type = _parse_context_type(source_type)
        target_ctx_type = _parse_context_type(target_type)
        manager.sync_contexts(source_ctx_type, target_ctx_type, keys)
        return True
    except Exception:
        return False


def context_keys(context_type: str) -> list[str]:
    """Get all keys in the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        List of all keys in the context, empty list if error
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        context = manager.get_context(ctx_type)
        return context.keys()
    except Exception:
        return []


def context_size(context_type: str) -> int:
    """Get the number of items in the specified context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        Number of key-value pairs in the context, 0 if error
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        context = manager.get_context(ctx_type)
        return context.size()
    except Exception:
        return 0


def context_info(context_type: str) -> dict[str, Any]:
    """Get information about a context.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        Dictionary with context information, empty dict if error
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        return manager.get_context_info(ctx_type)
    except Exception:
        return {}


def context_snapshot(context_type: str) -> dict[str, Any]:
    """Get a snapshot of the context data.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        Dictionary representation of the context, empty dict if error
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        return manager.get_context_snapshot(ctx_type)
    except Exception:
        return {}


def context_restore(context_type: str, snapshot: dict[str, Any]) -> bool:
    """Restore context from a snapshot.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        snapshot: Dictionary representation of the context
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        manager.restore_context_snapshot(ctx_type, snapshot)
        return True
    except Exception:
        return False


def context_types() -> list[str]:
    """Get all active context types.
    
    Returns:
        List of active context type names, empty list if error
    """
    try:
        manager = _get_context_manager()
        active_types = manager.get_all_context_types()
        return [ctx_type.value for ctx_type in active_types]
    except Exception:
        return []


def context_metrics() -> dict[str, Any]:
    """Get context manager metrics.
    
    Returns:
        Dictionary with performance and usage metrics, empty dict if error
    """
    try:
        manager = _get_context_manager()
        return manager.get_metrics()
    except Exception:
        return {}


# Advanced context operations

def context_merge(source_type: str, target_type: str) -> bool:
    """Merge all data from source context into target context.
    
    Args:
        source_type: Source context type ("environmental", "agent", "workflow")
        target_type: Target context type ("environmental", "agent", "workflow")
        
    Returns:
        True if successful, False otherwise
    """
    return context_sync(source_type, target_type, None)


def context_copy(source_type: str, target_type: str, keys: list[str]) -> bool:
    """Copy specific keys from source context to target context.
    
    Args:
        source_type: Source context type ("environmental", "agent", "workflow")
        target_type: Target context type ("environmental", "agent", "workflow")
        keys: List of keys to copy
        
    Returns:
        True if successful, False otherwise
    """
    return context_sync(source_type, target_type, keys)


def context_exists(context_type: str) -> bool:
    """Check if a context type has been created and has data.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        True if context exists and has data, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        context = manager.get_context(ctx_type)
        return context.size() > 0
    except Exception:
        return False


def context_is_empty(context_type: str) -> bool:
    """Check if a context is empty.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        True if context is empty, False otherwise
    """
    return context_size(context_type) == 0


# Utility functions for type conversion and validation

def to_context_dict(context_type: str) -> dict[str, Any]:
    """Convert context to a simple dictionary of key-value pairs.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        
    Returns:
        Dictionary of key-value pairs, empty dict if error
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        context = manager.get_context(ctx_type)
        return dict(context.items())
    except Exception:
        return {}


def from_context_dict(context_type: str, data: dict[str, Any]) -> bool:
    """Load context from a dictionary of key-value pairs.
    
    Args:
        context_type: Type of context ("environmental", "agent", "workflow")
        data: Dictionary of key-value pairs to load
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = _get_context_manager()
        ctx_type = _parse_context_type(context_type)
        
        # Clear existing context and load new data
        manager.clear_context(ctx_type)
        for key, value in data.items():
            manager.set_context_value(ctx_type, key, value)
        
        return True
    except Exception:
        return False


def context_validate_key(key: str) -> bool:
    """Validate if a key is valid for context storage.
    
    Args:
        key: The key to validate
        
    Returns:
        True if key is valid, False otherwise
    """
    try:
        manager = _get_context_manager()
        manager._validate_key(key)
        return True
    except Exception:
        return False


def context_validate_value(value: Any) -> bool:
    """Validate if a value is valid for context storage.
    
    Args:
        value: The value to validate
        
    Returns:
        True if value is valid, False otherwise
    """
    try:
        manager = _get_context_manager()
        manager._validate_value(value)
        return True
    except Exception:
        return False


# Configuration and management functions

def context_configure(settings_dict: dict[str, Any]) -> bool:
    """Configure the context manager with new settings.
    
    Args:
        settings_dict: Dictionary of configuration settings
        
    Returns:
        True if successful, False otherwise
    """
    try:
        global _context_manager
        settings = ContextSettings(**settings_dict)
        _context_manager = ContextManager(settings)
        return True
    except Exception:
        return False


def context_reset() -> bool:
    """Reset the context manager (clear all contexts and recreate).
    
    Returns:
        True if successful, False otherwise
    """
    try:
        global _context_manager
        _context_manager = ContextManager()
        return True
    except Exception:
        return False 