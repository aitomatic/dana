"""
Compatibility layer for legacy resource system

This module provides compatibility classes and modules for tests that expect
the old BaseResource API and context_integration module.
"""

from typing import Any

from dana.common.sys_resource.base_sys_resource import BaseSysResource

from .resource_state import ResourceState


class BaseResource(BaseSysResource):
    """Compatibility class for legacy BaseResource API.

    This provides the old BaseResource interface that tests expect,
    while using the new BaseSysResource as the underlying implementation.
    """

    def __init__(
        self,
        kind: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        domain: str = "general",
        tags: list[str] | None = None,
        capabilities: list[str] | None = None,
        permissions: list[str] | None = None,
    ):
        """Initialize BaseResource with legacy API."""
        super().__init__(name=name, description=description)
        self.kind = kind
        self.version = version
        self.domain = domain
        self.tags = tags or []
        self.capabilities = capabilities or []
        self.permissions = permissions or []
        self._state = ResourceState.CREATED

    @property
    def state(self) -> str:
        """Get current resource state."""
        return self._state

    def is_running(self) -> bool:
        """Check if resource is running."""
        return self._state == ResourceState.RUNNING

    def start(self) -> bool:
        """Start the resource."""
        if self._state == ResourceState.CREATED:
            self._state = ResourceState.RUNNING
            return True
        return False

    def stop(self) -> bool:
        """Stop the resource."""
        if self._state in [ResourceState.RUNNING, ResourceState.SUSPENDED]:
            self._state = ResourceState.TERMINATED
            return True
        return False

    def suspend(self) -> bool:
        """Suspend the resource."""
        if self._state == ResourceState.RUNNING:
            self._state = ResourceState.SUSPENDED
            return True
        return False

    def resume(self) -> bool:
        """Resume the resource."""
        if self._state == ResourceState.SUSPENDED:
            self._state = ResourceState.RUNNING
            return True
        return False

    def get_metadata(self) -> dict[str, Any]:
        """Get resource metadata."""
        return {
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "tags": self.tags,
            "capabilities": self.capabilities,
            "permissions": self.permissions,
        }


# Context integration compatibility
class AgentAccessError(Exception):
    """Error raised when agent access is denied."""

    pass


class ResourceContextIntegrator:
    """Compatibility class for resource context integration."""

    def __init__(self):
        self.resources = {}

    def register_resource(self, name: str, resource: BaseResource):
        """Register a resource."""
        self.resources[name] = resource

    def get_resource(self, name: str) -> BaseResource | None:
        """Get a resource by name."""
        return self.resources.get(name)


def get_resource_integrator() -> ResourceContextIntegrator:
    """Get the global resource integrator instance."""
    if not hasattr(get_resource_integrator, "_instance"):
        get_resource_integrator._instance = ResourceContextIntegrator()
    return get_resource_integrator._instance
