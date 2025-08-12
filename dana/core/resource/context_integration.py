"""
Resource Context Integration

This module provides integration between the resource system and SandboxContext,
including agent-only access validation.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from dana.common.exceptions import StateError
from .resource_registry import ResourceRegistry, ResourceError
from .resource_loader import ResourceLoader

if TYPE_CHECKING:
    from dana.core.lang.sandbox_context import SandboxContext


class AgentAccessError(Exception):
    """Exception raised when non-agent code tries to access resources."""

    pass


class ResourceContextIntegrator:
    """
    Integrates the resource system with SandboxContext.

    Provides agent-only access validation and resource management within
    the existing Dana runtime infrastructure.
    """

    def __init__(self):
        self.registry = ResourceRegistry()
        self.loader = ResourceLoader(self.registry)
        self._current_agent_context: Optional[str] = None
        self._initialized = False

        # Load all resources on first use
        self._ensure_loaded()

    def _ensure_loaded(self):
        """Ensure all resources are loaded."""
        if not self._initialized:
            self.loader.load_all()
            self._initialized = True

    def set_agent_context(self, agent_name: str):
        """Set the current agent context for resource access validation."""
        self._current_agent_context = agent_name

    def clear_agent_context(self):
        """Clear the current agent context."""
        self._current_agent_context = None

    def validate_agent_access(self) -> str:
        """
        Validate that resource access is happening within an agent context.

        Returns:
            The current agent name

        Raises:
            AgentAccessError: If no agent context is active
        """
        if self._current_agent_context is None:
            raise AgentAccessError(
                "Resources can only be accessed within agent contexts. "
                "Ensure resource operations are called from within an agent method."
            )
        return self._current_agent_context

    def create_resource(self, kind: str, name: str, sandbox_context: "SandboxContext", **kwargs):
        """
        Create a resource and integrate it with SandboxContext.

        Args:
            kind: Resource type (e.g., "mcp", "rag")
            name: Resource name
            sandbox_context: The sandbox context to integrate with
            **kwargs: Resource-specific configuration

        Returns:
            The created resource instance
        """
        # Validate agent access
        agent_name = self.validate_agent_access()

        # Create resource through registry
        resource = self.registry.create_resource(kind, name, agent_name, **kwargs)

        # Integrate with SandboxContext using existing set_resource method
        sandbox_context.set_resource(name, resource)

        return resource

    def get_resource(self, name: str, sandbox_context: "SandboxContext"):
        """
        Get a resource with agent access validation.

        Args:
            name: Resource name
            sandbox_context: The sandbox context

        Returns:
            The resource instance
        """
        # Validate agent access
        self.validate_agent_access()

        # Use existing get_resource method from SandboxContext
        try:
            return sandbox_context.get_resource(name)
        except KeyError:
            raise ResourceError(f"Resource '{name}' not found", name)

    def invoke_resource_method(self, resource_name: str, method_name: str, sandbox_context: "SandboxContext", *args, **kwargs):
        """
        Invoke a resource method with agent access validation.

        Args:
            resource_name: Name of the resource
            method_name: Name of the method to call
            sandbox_context: The sandbox context
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method call
        """
        # Validate agent access
        agent_name = self.validate_agent_access()

        # Get resource
        resource = self.get_resource(resource_name, sandbox_context)

        # Check ownership
        if resource.owner_agent != agent_name:
            raise AgentAccessError(
                f"Agent '{agent_name}' cannot access resource '{resource_name}' " f"owned by agent '{resource.owner_agent}'"
            )

        # Check if method exists
        if not hasattr(resource, method_name):
            raise ResourceError(f"Resource '{resource_name}' has no method '{method_name}'")

        method = getattr(resource, method_name)
        if not callable(method):
            raise ResourceError(f"'{method_name}' is not a callable method on resource '{resource_name}'")

        # Call the method
        return method(*args, **kwargs)

    def list_agent_resources(self, agent_name: str = None) -> List[Any]:
        """List resources accessible to the current agent."""
        if agent_name is None:
            agent_name = self.validate_agent_access()

        return self.registry.list_resources(agent_name)

    def transfer_resource(self, resource_name: str, from_agent: str, to_agent: str) -> bool:
        """Transfer resource between agents."""
        # Only the owning agent can initiate transfers
        current_agent = self.validate_agent_access()
        if current_agent != from_agent:
            raise AgentAccessError(f"Only agent '{from_agent}' can transfer resource '{resource_name}'")

        return self.registry.transfer_resource(resource_name, from_agent, to_agent)

    def create_resource_handle(self, resource_name: str):
        """Create a portable handle for resource transfer."""
        # Validate agent access and ownership
        agent_name = self.validate_agent_access()
        resource = self.registry.get_resource(resource_name)

        if resource is None:
            raise ResourceError(f"Resource '{resource_name}' not found", resource_name)

        if resource.owner_agent != agent_name:
            raise AgentAccessError(f"Agent '{agent_name}' cannot create handle for resource owned by '{resource.owner_agent}'")

        return self.registry.create_handle(resource_name)

    def create_from_handle(self, handle, agent_name: str = None):
        """Create a resource from a portable handle."""
        if agent_name is None:
            agent_name = self.validate_agent_access()

        return self.registry.create_from_handle(handle, agent_name)

    def cleanup_agent_resources(self, agent_name: str):
        """Clean up all resources owned by an agent."""
        self.registry.cleanup_agent_resources(agent_name)

    def get_statistics(self) -> Dict[str, Any]:
        """Get resource system statistics."""
        stats = self.registry.get_statistics()
        stats["plugins"] = len(self.loader.plugins)
        stats["search_paths"] = [str(p) for p in self.loader.search_paths]
        return stats

    def register_user_resource(self, name: str, kind: str, blueprint_class=None, factory_func=None, metadata=None):
        """
        Register a user-defined resource at runtime.

        This allows Dana code to dynamically register new resource types.
        """
        self.loader.register_user_resource(name, kind, blueprint_class, factory_func, metadata)

    def reload_resources(self):
        """Reload all resource plugins from disk."""
        self._initialized = False
        self.loader.plugins.clear()
        self._ensure_loaded()


# Global instance for integration with Dana runtime
_resource_integrator = ResourceContextIntegrator()


def get_resource_integrator() -> ResourceContextIntegrator:
    """Get the global resource context integrator instance."""
    return _resource_integrator


# Convenience functions that can be imported by the Dana runtime
def create_resource(kind: str, name: str, sandbox_context: "SandboxContext", **kwargs):
    """Create a resource with agent validation."""
    return _resource_integrator.create_resource(kind, name, sandbox_context, **kwargs)


def get_resource(name: str, sandbox_context: "SandboxContext"):
    """Get a resource with agent validation."""
    return _resource_integrator.get_resource(name, sandbox_context)


def invoke_resource_method(resource_name: str, method_name: str, sandbox_context: "SandboxContext", *args, **kwargs):
    """Invoke resource method with agent validation."""
    return _resource_integrator.invoke_resource_method(resource_name, method_name, sandbox_context, *args, **kwargs)


def set_agent_context(agent_name: str):
    """Set current agent context for resource access validation."""
    _resource_integrator.set_agent_context(agent_name)


def clear_agent_context():
    """Clear current agent context."""
    _resource_integrator.clear_agent_context()
