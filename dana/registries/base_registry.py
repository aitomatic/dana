"""
Base Registry class for all Dana runtime registries.

Provides common patterns and interfaces for registry implementations.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, Union

from dana.common.mixins.registerable import Registerable

# Type variables for generic registry
T = TypeVar("T")  # The type being registered (e.g., StructType, FunctionType)
K = TypeVar("K")  # The key type (usually str, but could be tuple for composite keys)


class BaseRegistry(Generic[K, T], ABC):
    """Abstract base class for all Dana registries.

    Provides common patterns:
    - Singleton pattern
    - Registration/lookup operations
    - Validation and conflict resolution
    - Integration with Registerable mixin
    - Testing support (clear)
    """

    _instance: Optional["BaseRegistry"] = None
    _storage: dict[K, T] = {}

    def __new__(cls) -> "BaseRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_storage()
        return cls._instance

    def _initialize_storage(self) -> None:
        """Initialize storage for this registry instance."""
        # Each concrete registry class gets its own storage
        registry_class = self.__class__
        if not hasattr(registry_class, "_storage"):
            registry_class._storage = {}
        # Ensure we're using the concrete class's storage, not the base class's
        if hasattr(BaseRegistry, "_storage") and registry_class._storage is BaseRegistry._storage:
            registry_class._storage = {}

    @classmethod
    @abstractmethod
    def register(cls, item: T, key: K | None = None, overwrite: bool = False, **kwargs) -> None:
        """Register an item in the registry.

        Args:
            item: The item to register
            key: Optional key (if None, should be derived from item)
            overwrite: Whether to overwrite existing item (backward compatibility)
            **kwargs: Additional registration options
        """
        pass

    @classmethod
    @abstractmethod
    def get(cls, key: K) -> T | None:
        """Get an item by key.

        Args:
            key: The key to lookup

        Returns:
            The registered item or None if not found
        """
        pass

    @classmethod
    def exists(cls, key: K) -> bool:
        """Check if an item exists in the registry.

        Args:
            key: The key to check

        Returns:
            True if the item exists
        """
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        return key in storage

    @classmethod
    def list_all(cls) -> list[K]:
        """List all registered keys.

        Returns:
            List of all keys in registration order
        """
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        return list(storage.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered items (for testing)."""
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        storage.clear()

    @classmethod
    def count(cls) -> int:
        """Get the number of registered items."""
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        return len(storage)

    def __len__(self) -> int:
        """Support len() builtin function."""
        return self.count()

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return self.count() == 0

    # === Integration with Registerable mixin ===

    @classmethod
    def register_object(cls, obj: Union[T, Registerable], **kwargs) -> None:
        """Register an object, handling Registerable mixin if present.

        Args:
            obj: Object to register
            **kwargs: Additional registration options
        """
        # If object is Registerable, add to its global registry too
        if isinstance(obj, Registerable):
            obj.add_to_registry()

        # Extract key based on object type
        key = cls._extract_key(obj)
        cls.register(obj, key, **kwargs)

    @classmethod
    @abstractmethod
    def _extract_key(cls, item: T) -> K:
        """Extract the registration key from an item.

        Args:
            item: The item to extract key from

        Returns:
            The key for registration
        """
        pass

    # === Validation and conflict resolution ===

    @classmethod
    def _validate_registration(cls, item: T, key: K, existing: T | None = None) -> bool:
        """Validate if an item can be registered.

        Args:
            item: Item to register
            key: Key for registration
            existing: Existing item at that key (if any)

        Returns:
            True if registration is valid

        Raises:
            ValueError: If registration conflicts with existing item
        """
        if existing is None:
            return True

        # Default: allow idempotent registration of same object
        if existing is item:
            return True

        # Subclasses can override for more sophisticated validation
        return cls._handle_registration_conflict(item, key, existing)

    @classmethod
    def _handle_registration_conflict(cls, item: T, key: K, existing: T) -> bool:
        """Handle registration conflicts.

        Default behavior: raise ValueError
        Subclasses can override for custom conflict resolution.

        Args:
            item: New item being registered
            key: Registration key
            existing: Existing item at that key

        Returns:
            True if conflict is resolved and registration should proceed

        Raises:
            ValueError: If conflict cannot be resolved
        """
        raise ValueError(f"Item already registered at key '{key}'. Use overwrite=True to force.")

    # === Events and hooks ===

    @classmethod
    def _on_register(cls, item: T, key: K) -> None:
        """Hook called after successful registration.

        Args:
            item: The registered item
            key: The registration key
        """
        pass

    @classmethod
    def _on_unregister(cls, item: T, key: K) -> None:
        """Hook called after item removal.

        Args:
            item: The removed item
            key: The registration key
        """
        pass


class NamedItemRegistry(BaseRegistry[str, T]):
    """Registry for items that have a 'name' attribute."""

    @classmethod
    def _extract_key(cls, item: T) -> str:
        """Extract name from item."""
        if hasattr(item, "name"):
            return str(item.name)
        elif hasattr(item, "__name__"):
            return str(item.__name__)
        else:
            raise ValueError(f"Item {item} has no 'name' or '__name__' attribute")

    @classmethod
    def register(cls, item: T, key: str | None = None, overwrite: bool = False) -> None:
        """Register a named item.

        Args:
            item: Item to register
            key: Optional key (defaults to item.name)
            overwrite: Whether to allow overwriting existing items
        """
        if key is None:
            key = cls._extract_key(item)

        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        existing = storage.get(key)
        if not overwrite and existing is not None:
            if not cls._validate_registration(item, key, existing):
                return  # Validation failed but didn't raise

        storage[key] = item
        cls._on_register(item, key)

    @classmethod
    def get(cls, key: str) -> T | None:
        """Get item by name."""
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        return storage.get(key)

    @classmethod
    def get_or_raise(cls, key: str, error_msg: str | None = None) -> T:
        """Get item by name or raise ValueError.

        Args:
            key: The key to lookup
            error_msg: Optional custom error message

        Returns:
            The registered item

        Raises:
            ValueError: If item not found
        """
        item = cls.get(key)
        if item is None:
            if error_msg is None:
                available = sorted(cls.list_all())
                error_msg = f"Item '{key}' not found. Available: {available}"
            raise ValueError(error_msg)
        return item


class CompositeKeyRegistry(BaseRegistry[tuple, T]):
    """Registry for items with composite keys (e.g., method registry with (type, name))."""

    @classmethod
    def register(cls, item: T, key: tuple, overwrite: bool = False) -> None:
        """Register item with composite key."""
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        existing = storage.get(key)
        if not overwrite and existing is not None:
            if not cls._validate_registration(item, key, existing):
                return

        storage[key] = item
        cls._on_register(item, key)

    @classmethod
    def get(cls, key: tuple) -> T | None:
        """Get item by composite key."""
        # Use the concrete class's storage
        storage = getattr(cls, "_storage", {})
        return storage.get(key)

    @classmethod
    def find_by_partial_key(cls, **filters) -> list[tuple[tuple, T]]:
        """Find items by partial key matching.

        Args:
            **filters: Key-value filters for tuple positions

        Returns:
            List of (key, item) tuples matching filters
        """
        results = []
        for key, item in cls._storage.items():
            if cls._matches_filters(key, filters):
                results.append((key, item))
        return results

    @classmethod
    def _matches_filters(cls, key: tuple, filters: dict) -> bool:
        """Check if a key matches the given filters."""
        # Subclasses should override this for specific key structures
        return True
