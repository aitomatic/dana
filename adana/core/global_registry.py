"""
Global Registry for Multi-Agent, Resource, and Workflow Discovery

This module provides discovery, registration, and routing capabilities
for agents, resources, and workflows in the Adana agentic architecture.
"""

from collections.abc import Callable
from datetime import datetime
import threading
from typing import Any, TypeVar
import uuid

from adana.common.protocols import AgentProtocol, ResourceProtocol, WorkflowProtocol


T = TypeVar("T")


class BaseRegistry[T]:
    """
    Generic registry for managing discoverable objects (agents, resources, workflows).

    Provides thread-safe registration, discovery, and metadata management.
    """

    def __init__(self, registry_type: str):
        """
        Initialize the registry.

        Args:
            registry_type: Type of registry (e.g., "agents", "resources", "workflows")
        """
        self.registry_type = registry_type
        self._items: dict[str, T] = {}
        self._lock = threading.Lock()

    def register(
        self,
        item: T,
        object_id: str | None = None,
        item_type: str = "",
        name: str = "",
        description: str = "",
        capabilities: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Register an item with the registry.

        Args:
            item: The object to register
            object_id: Optional ID (will use item.object_id or generate UUID)
            item_type: Type/category of item
            name: Human-readable name
            description: Description of what the item does
            capabilities: List of capabilities
            metadata: Additional metadata

        Returns:
            Object ID assigned to the item
        """
        with self._lock:
            # Use provided object_id or the item's object_id, or generate one
            final_object_id = object_id or getattr(item, "object_id", None) or str(uuid.uuid4())

            # Store the item
            self._items[final_object_id] = item

            # Update item with its ID if it has object_id attribute
            if hasattr(item, "object_id"):
                item.object_id = final_object_id

            # Store metadata on the item
            if hasattr(item, "_registered_capabilities"):
                item._registered_capabilities = capabilities or []
            if hasattr(item, "_registered_metadata"):
                item._registered_metadata = metadata or {}
            if hasattr(item, "_registered_type"):
                item._registered_type = item_type
            if hasattr(item, "_registered_name"):
                item._registered_name = name
            if hasattr(item, "_registered_description"):
                item._registered_description = description

            return final_object_id

    def unregister(self, object_id: str) -> bool:
        """
        Unregister an item from the registry.

        Args:
            object_id: ID of the item to unregister

        Returns:
            True if item was unregistered, False if not found
        """
        with self._lock:
            if object_id in self._items:
                del self._items[object_id]
                return True
            return False

    def get(self, object_id: str) -> T | None:
        """
        Get an item by ID.

        Args:
            object_id: ID of the item

        Returns:
            Item if found, None otherwise
        """
        return self._items.get(object_id)

    def get_info(self, object_id: str) -> dict[str, Any] | None:
        """
        Get information about a specific item.

        Args:
            object_id: ID of the item

        Returns:
            Item info dict if found, None otherwise
        """
        item = self._items.get(object_id)
        if not item:
            return None

        return {
            "object_id": object_id,
            "registry_type": self.registry_type,
            "item_type": getattr(item, "_registered_type", getattr(item, "resource_type", getattr(item, "agent_type", "unknown"))),
            "name": getattr(item, "_registered_name", f"{self.registry_type}_item"),
            "description": getattr(item, "_registered_description", getattr(item, "prt_public_description", "No description available")),
            "capabilities": getattr(item, "_registered_capabilities", []),
            "status": "active",
            "metadata": getattr(item, "_registered_metadata", {}),
        }

    def list(self, item_type: str | None = None, capability: str | None = None, filter_fn: Callable[[T], bool] | None = None) -> list[T]:
        """
        List items with optional filtering.

        Args:
            item_type: Filter by item type
            capability: Filter by capability
            filter_fn: Custom filter function

        Returns:
            List of matching items
        """
        items = list(self._items.values())

        if item_type:
            items = [
                i for i in items if getattr(i, "_registered_type", getattr(i, "resource_type", getattr(i, "agent_type", None))) == item_type
            ]

        if capability:
            items = [i for i in items if capability in getattr(i, "_registered_capabilities", [])]

        if filter_fn:
            items = [i for i in items if filter_fn(i)]

        return items

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        with self._lock:
            total_items = len(self._items)
            type_counts = {}

            for item in self._items.values():
                item_type = getattr(item, "_registered_type", getattr(item, "resource_type", getattr(item, "agent_type", "unknown")))
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

            return {
                "registry_type": self.registry_type,
                "total_items": total_items,
                "type_counts": type_counts,
            }


class AgentRegistry(BaseRegistry[AgentProtocol]):
    """
    Registry for managing agent discovery and routing.

    Provides centralized agent management for multi-agent communication.
    """

    def __init__(self):
        """Initialize the agent registry."""
        super().__init__(registry_type="agents")

    def update_agent_status(self, object_id: str, status: str) -> bool:
        """Update an agent's status."""
        with self._lock:
            if object_id in self._items:
                if hasattr(self._items[object_id], "status"):
                    self._items[object_id].status = status
                if hasattr(self._items[object_id], "last_seen"):
                    self._items[object_id].last_seen = datetime.now().isoformat()
                return True
            return False

    def update_agent_metadata(self, object_id: str, metadata: dict[str, Any]) -> bool:
        """Update an agent's metadata."""
        with self._lock:
            if object_id in self._items:
                if hasattr(self._items[object_id], "metadata"):
                    self._items[object_id].metadata.update(metadata)
                if hasattr(self._items[object_id], "last_seen"):
                    self._items[object_id].last_seen = datetime.now().isoformat()
                return True
            return False

    def export_registry(self) -> dict[str, Any]:
        """Export registry data for persistence."""
        with self._lock:
            return {
                "agents": {aid: getattr(agent, "agent_type", "unknown") for aid, agent in self._items.items()},
                "exported_at": datetime.now().isoformat(),
            }

    def import_registry(self, data: dict[str, Any]) -> bool:
        """Import registry data from persistence."""
        with self._lock:
            try:
                self._items.clear()
                return True
            except Exception:
                return False


class ResourceRegistry(BaseRegistry[ResourceProtocol]):
    """
    Registry for managing resource discovery and access.

    Provides centralized resource management for multi-agent communication.
    """

    def __init__(self):
        """Initialize the resource registry."""
        super().__init__(registry_type="resources")


class WorkflowRegistry(BaseRegistry[WorkflowProtocol]):
    """
    Registry for managing workflow discovery and execution.

    Provides centralized workflow management for multi-agent communication.
    """

    def __init__(self):
        """Initialize the workflow registry."""
        super().__init__(registry_type="workflows")


# Global registries
_global_registries: dict[str, BaseRegistry] | None = None


def get_global_registry() -> dict[str, BaseRegistry]:
    """
    Get the global registry dict containing all registry types.

    Returns:
        Dictionary with keys: "agents", "resources", "workflows"
    """
    global _global_registries
    if _global_registries is None:
        _global_registries = {
            "agents": AgentRegistry(),
            "resources": ResourceRegistry(),
            "workflows": WorkflowRegistry(),
        }
    return _global_registries


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance (backward compatible).

    Returns:
        Global AgentRegistry instance
    """
    return get_global_registry()["agents"]  # type: ignore


def get_resource_registry() -> ResourceRegistry:
    """
    Get the global resource registry instance.

    Returns:
        Global ResourceRegistry instance
    """
    return get_global_registry()["resources"]  # type: ignore


def get_workflow_registry() -> WorkflowRegistry:
    """
    Get the global workflow registry instance.

    Returns:
        Global WorkflowRegistry instance
    """
    return get_global_registry()["workflows"]  # type: ignore


def set_global_registry(registries: dict[str, BaseRegistry]) -> None:
    """
    Set the global registries.

    Args:
        registries: Dictionary with registry instances
    """
    global _global_registries
    _global_registries = registries
