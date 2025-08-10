"""
Resource Registry

This module provides the ResourceRegistry for managing resource instances
and the ResourceError exception class.
"""

from typing import Any, Dict, List, Optional, Type, Callable
from .base_resource import BaseResource, ResourceState
from .resource_handle import ResourceHandle


class ResourceError(Exception):
    """Exception raised for resource-related errors."""

    def __init__(self, message: str, resource_name: str = "", original_error: Exception = None):
        super().__init__(message)
        self.resource_name = resource_name
        self.original_error = original_error


class ResourceRegistry:
    """
    Registry for managing resource instances within a sandbox context.

    Handles resource creation, lifecycle management, and transfer operations.
    """

    def __init__(self):
        self._resources: Dict[str, BaseResource] = {}
        self._blueprints: Dict[str, Type[BaseResource]] = {}
        self._factories: Dict[str, Callable] = {}  # Factory functions for dynamic resources
        self._agent_resources: Dict[str, List[str]] = {}  # agent -> resource names
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}  # Plugin metadata

    def register_blueprint(self, name: str, blueprint_class: Type[BaseResource], metadata: Dict[str, Any] = None):
        """Register a resource blueprint type."""
        self._blueprints[name] = blueprint_class
        if metadata:
            self._plugin_metadata[name] = metadata

    def register_factory(self, name: str, factory_func: Callable, metadata: Dict[str, Any] = None):
        """Register a resource factory function for dynamic creation."""
        self._factories[name] = factory_func
        if metadata:
            self._plugin_metadata[name] = metadata

    def create_resource(self, kind: str, name: str, agent_name: str, **kwargs) -> BaseResource:
        """Create a new resource instance."""
        resource = None

        # Check blueprints first
        if kind in self._blueprints:
            blueprint_class = self._blueprints[kind]
            resource = blueprint_class(name=name, kind=kind, owner_agent=agent_name, **kwargs)
        # Check factories
        elif kind in self._factories:
            factory_func = self._factories[kind]
            resource = factory_func(name=name, kind=kind, owner_agent=agent_name, **kwargs)
        else:
            raise ResourceError(f"Unknown resource kind: {kind}")

        if name in self._resources:
            raise ResourceError(f"Resource with name '{name}' already exists", name)

        # Register resource
        self._resources[name] = resource

        # Track agent ownership
        if agent_name not in self._agent_resources:
            self._agent_resources[agent_name] = []
        self._agent_resources[agent_name].append(name)

        return resource

    def get_resource(self, name: str) -> Optional[BaseResource]:
        """Get resource by name."""
        return self._resources.get(name)

    def list_resources(self, agent_name: str = None) -> List[BaseResource]:
        """List all resources or resources owned by specific agent."""
        if agent_name is None:
            return list(self._resources.values())

        agent_resource_names = self._agent_resources.get(agent_name, [])
        return [self._resources[name] for name in agent_resource_names if name in self._resources]

    def transfer_resource(self, resource_name: str, from_agent: str, to_agent: str) -> bool:
        """Transfer resource ownership between agents."""
        if resource_name not in self._resources:
            raise ResourceError(f"Resource '{resource_name}' not found", resource_name)

        resource = self._resources[resource_name]
        if resource.owner_agent != from_agent:
            raise ResourceError(f"Agent '{from_agent}' does not own resource '{resource_name}'", resource_name)

        # Transfer ownership
        resource.owner_agent = to_agent

        # Update tracking
        if from_agent in self._agent_resources:
            if resource_name in self._agent_resources[from_agent]:
                self._agent_resources[from_agent].remove(resource_name)

        if to_agent not in self._agent_resources:
            self._agent_resources[to_agent] = []
        self._agent_resources[to_agent].append(resource_name)

        return True

    def create_handle(self, resource_name: str) -> ResourceHandle:
        """Create a portable handle for resource transfer."""
        if resource_name not in self._resources:
            raise ResourceError(f"Resource '{resource_name}' not found", resource_name)

        resource = self._resources[resource_name]
        metadata = resource.get_metadata()

        return ResourceHandle(
            kind=metadata["kind"],
            name=metadata["name"],
            version=metadata["version"],
            description=metadata["description"],
            domain=metadata["domain"],
            tags=metadata["tags"],
            capabilities=metadata["capabilities"],
            permissions=metadata["permissions"],
            config=resource.config.copy(),  # Deep copy for safety
            source_agent=resource.owner_agent,
        )

    def create_from_handle(self, handle: ResourceHandle, agent_name: str) -> BaseResource:
        """Create a resource from a handle (best-effort reconstruction)."""
        if not handle.validate():
            raise ResourceError("Invalid resource handle")

        if not handle.is_compatible_with(handle.kind):
            raise ResourceError(f"Handle kind mismatch: {handle.kind}")

        # Try to create resource from handle data
        return self.create_resource(
            kind=handle.kind,
            name=handle.name,
            agent_name=agent_name,
            version=handle.version,
            description=handle.description,
            domain=handle.domain,
            tags=handle.tags,
            capabilities=handle.capabilities,
            permissions=handle.permissions,
            **handle.config,
        )

    def cleanup_agent_resources(self, agent_name: str):
        """Clean up all resources owned by an agent."""
        if agent_name not in self._agent_resources:
            return

        resource_names = self._agent_resources[agent_name].copy()
        for resource_name in resource_names:
            if resource_name in self._resources:
                resource = self._resources[resource_name]
                resource.cleanup()
                del self._resources[resource_name]

        del self._agent_resources[agent_name]

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        state_counts = {}
        for resource in self._resources.values():
            state = resource.state.value
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            "total_resources": len(self._resources),
            "total_agents": len(self._agent_resources),
            "registered_blueprints": list(self._blueprints.keys()),
            "registered_factories": list(self._factories.keys()),
            "state_distribution": state_counts,
            "plugin_count": len(self._plugin_metadata),
        }

    def list_available_kinds(self) -> List[str]:
        """List all available resource kinds."""
        return list(set(list(self._blueprints.keys()) + list(self._factories.keys())))

    def get_plugin_metadata(self, kind: str) -> Dict[str, Any]:
        """Get metadata for a resource plugin."""
        return self._plugin_metadata.get(kind, {})
