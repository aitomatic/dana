"""
Resource Context Integration

This module provides integration between resources and agent contexts.
"""

from .compatibility import BaseResource


class ResourceContextIntegrator:
    """Integrates resources with agent contexts."""

    def __init__(self):
        self.resources = {}

    def register_resource(self, name: str, resource: BaseResource):
        """Register a resource in the context."""
        self.resources[name] = resource

    def get_resource(self, name: str) -> BaseResource | None:
        """Get a resource by name."""
        return self.resources.get(name)

    def remove_resource(self, name: str) -> bool:
        """Remove a resource from the context."""
        if name in self.resources:
            del self.resources[name]
            return True
        return False


def get_resource_integrator() -> ResourceContextIntegrator:
    """Get the global resource integrator instance."""
    if not hasattr(get_resource_integrator, "_instance"):
        get_resource_integrator._instance = ResourceContextIntegrator()
    return get_resource_integrator._instance
