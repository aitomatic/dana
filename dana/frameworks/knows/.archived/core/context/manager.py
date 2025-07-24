"""Context manager for handling different types of contexts."""

import threading
from datetime import datetime, timedelta
from typing import Any

from dana.frameworks.knows.core.context.base import Context, ContextError, ContextSyncError, ContextType
from dana.frameworks.knows.core.context.config import ContextSettings


class ContextManager:
    """Manages different types of context with thread safety and caching."""
    
    def __init__(self, settings: ContextSettings | None = None):
        """Initialize the context manager.
        
        Args:
            settings: Configuration settings for context management
        """
        self.settings = settings or ContextSettings()
        self.contexts: dict[ContextType, Context] = {}
        self._lock = threading.RLock()
        self._cache: dict[str, tuple[Context, datetime]] = {}
        self._metrics: dict[str, Any] = {
            "contexts_created": 0,
            "contexts_accessed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "sync_operations": 0,
            "sync_failures": 0
        }
    
    def get_context(self, context_type: ContextType) -> Context:
        """Get or create a context of the specified type.
        
        Args:
            context_type: The type of context to retrieve
            
        Returns:
            The context instance for the specified type
        """
        with self._lock:
            self._metrics["contexts_accessed"] += 1
            
            if context_type not in self.contexts:
                self.contexts[context_type] = Context(context_type)
                self._metrics["contexts_created"] += 1
            
            return self.contexts[context_type]
    
    def set_context_value(self, context_type: ContextType, key: str, value: Any) -> None:
        """Set a value in the specified context.
        
        Args:
            context_type: The type of context
            key: The key to set
            value: The value to store
            
        Raises:
            ContextError: If validation fails
        """
        self._validate_key(key)
        self._validate_value(value)
        
        context = self.get_context(context_type)
        context.set(key, value)
        
        # Invalidate cache for this context
        self._invalidate_cache(context_type)
    
    def get_context_value(self, context_type: ContextType, key: str, default: Any = None) -> Any:
        """Get a value from the specified context.
        
        Args:
            context_type: The type of context
            key: The key to retrieve
            default: Default value if key not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        context = self.get_context(context_type)
        return context.get(key, default)
    
    def has_context_value(self, context_type: ContextType, key: str) -> bool:
        """Check if a key exists in the specified context.
        
        Args:
            context_type: The type of context
            key: The key to check
            
        Returns:
            True if key exists, False otherwise
        """
        context = self.get_context(context_type)
        return context.has(key)
    
    def remove_context_value(self, context_type: ContextType, key: str) -> bool:
        """Remove a key from the specified context.
        
        Args:
            context_type: The type of context
            key: The key to remove
            
        Returns:
            True if key was removed, False if key didn't exist
        """
        context = self.get_context(context_type)
        removed = context.remove(key)
        
        if removed:
            self._invalidate_cache(context_type)
        
        return removed
    
    def clear_context(self, context_type: ContextType) -> None:
        """Clear all data in the specified context.
        
        Args:
            context_type: The type of context to clear
        """
        with self._lock:
            if context_type in self.contexts:
                self.contexts[context_type].clear()
                self._invalidate_cache(context_type)
    
    def clear_all_contexts(self) -> None:
        """Clear all contexts."""
        with self._lock:
            for context in self.contexts.values():
                context.clear()
            self._cache.clear()
    
    def sync_contexts(self, source_type: ContextType, target_type: ContextType, 
                     keys: list[str] | None = None) -> None:
        """Synchronize data between contexts.
        
        Args:
            source_type: The source context type
            target_type: The target context type
            keys: Optional list of specific keys to sync (sync all if None)
            
        Raises:
            ContextSyncError: If synchronization fails
        """
        try:
            with self._lock:
                self._metrics["sync_operations"] += 1
                
                source_context = self.get_context(source_type)
                target_context = self.get_context(target_type)
                
                if keys is None:
                    # Sync all keys
                    target_context.merge(source_context)
                else:
                    # Sync specific keys
                    for key in keys:
                        if source_context.has(key):
                            target_context.set(key, source_context.get(key))
                
                self._invalidate_cache(target_type)
                
        except Exception as e:
            self._metrics["sync_failures"] += 1
            raise ContextSyncError(f"Failed to sync contexts: {e}")
    
    def get_context_snapshot(self, context_type: ContextType) -> dict[str, Any]:
        """Get a snapshot of the context data.
        
        Args:
            context_type: The type of context
            
        Returns:
            Dictionary representation of the context
        """
        context = self.get_context(context_type)
        return context.to_dict()
    
    def restore_context_snapshot(self, context_type: ContextType, snapshot: dict[str, Any]) -> None:
        """Restore context from a snapshot.
        
        Args:
            context_type: The type of context
            snapshot: Dictionary representation of the context
            
        Raises:
            ContextError: If restoration fails
        """
        try:
            with self._lock:
                restored_context = Context.from_dict(snapshot)
                if restored_context.type != context_type:
                    raise ContextError(f"Context type mismatch: expected {context_type}, got {restored_context.type}")
                
                self.contexts[context_type] = restored_context
                self._invalidate_cache(context_type)
                
        except Exception as e:
            raise ContextError(f"Failed to restore context: {e}")
    
    def get_all_context_types(self) -> list[ContextType]:
        """Get all active context types.
        
        Returns:
            List of all context types that have been created
        """
        with self._lock:
            return list(self.contexts.keys())
    
    def get_context_info(self, context_type: ContextType) -> dict[str, Any]:
        """Get information about a context.
        
        Args:
            context_type: The type of context
            
        Returns:
            Dictionary with context information
        """
        context = self.get_context(context_type)
        return {
            "type": context.type.value,
            "size": context.size(),
            "keys": context.keys(),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
    
    def get_metrics(self) -> dict[str, Any]:
        """Get context manager metrics.
        
        Returns:
            Dictionary with performance and usage metrics
        """
        with self._lock:
            return {
                **self._metrics,
                "active_contexts": len(self.contexts),
                "cache_size": len(self._cache),
                "cache_hit_rate": (
                    self._metrics["cache_hits"] / 
                    max(1, self._metrics["cache_hits"] + self._metrics["cache_misses"])
                )
            }
    
    def _validate_key(self, key: str) -> None:
        """Validate a context key.
        
        Args:
            key: The key to validate
            
        Raises:
            ContextError: If key is invalid
        """
        if not isinstance(key, str) or not key.strip():
            raise ContextError("Key must be a non-empty string")
        
        if len(key) > self.settings.max_key_length:
            raise ContextError(f"Key length exceeds maximum of {self.settings.max_key_length}")
    
    def _validate_value(self, value: Any) -> None:
        """Validate a context value.
        
        Args:
            value: The value to validate
            
        Raises:
            ContextError: If value is invalid
        """
        # Simple size check - in production, this would be more sophisticated
        try:
            import sys
            value_size = sys.getsizeof(value)
            if value_size > self.settings.max_value_size:
                raise ContextError(f"Value size exceeds maximum of {self.settings.max_value_size} bytes")
        except (TypeError, OverflowError):
            # If we can't determine size, allow it
            pass
    
    def _invalidate_cache(self, context_type: ContextType) -> None:
        """Invalidate cache entries for a context type.
        
        Args:
            context_type: The context type to invalidate
        """
        cache_key = f"context_{context_type.value}"
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, (_, timestamp) in self._cache.items():
            if now - timestamp > timedelta(seconds=self.settings.cache_ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
    
    def __str__(self) -> str:
        """String representation of the context manager."""
        return f"ContextManager(contexts={len(self.contexts)}, cache_size={len(self._cache)})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the context manager."""
        return (f"ContextManager(contexts={list(self.contexts.keys())}, "
                f"cache_size={len(self._cache)}, settings={self.settings})") 