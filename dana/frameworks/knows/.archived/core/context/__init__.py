"""Context Management module for Dana KNOWS framework."""

from dana.frameworks.knows.core.context.base import Context, ContextError, ContextSyncError, ContextType, ContextValidationError
from dana.frameworks.knows.core.context.config import ContextSettings

# Import Dana functions for easy access
from dana.frameworks.knows.core.context.dana import (
    context_clear,
    context_clear_all,
    context_configure,
    context_copy,
    context_exists,
    context_get,
    context_has,
    context_info,
    context_is_empty,
    context_keys,
    context_merge,
    context_metrics,
    context_remove,
    context_reset,
    context_restore,
    context_set,
    context_size,
    context_snapshot,
    context_sync,
    context_types,
    context_validate_key,
    context_validate_value,
    from_context_dict,
    to_context_dict,
)
from dana.frameworks.knows.core.context.manager import ContextManager

__all__ = [
    # Core classes
    "Context",
    "ContextType", 
    "ContextManager",
    
    # Configuration
    "ContextSettings",
    
    # Exceptions
    "ContextError",
    "ContextSyncError", 
    "ContextValidationError",
    
    # Dana integration functions
    "context_set", "context_get", "context_has", "context_remove", "context_clear",
    "context_clear_all", "context_sync", "context_keys", "context_size", "context_info",
    "context_snapshot", "context_restore", "context_types", "context_metrics",
    "context_merge", "context_copy", "context_exists", "context_is_empty",
    "to_context_dict", "from_context_dict", "context_validate_key", "context_validate_value",
    "context_configure", "context_reset"
] 