"""
Resource Helpers

Helper functions for working with resources in Dana code.
These functions are designed to be imported and used in Dana scripts.
"""

from typing import Any, Dict, Optional, Callable
from pathlib import Path

from .context_integration import get_resource_integrator
from .base_resource import BaseResource


def register_resource(name: str, kind: str, factory_func: Callable, metadata: Dict[str, Any] = None):
    """
    Register a custom resource type at runtime.

    This function can be called from Dana code to register new resource types:

    ```dana
    from dana.core.resource.resource_helpers import register_resource

    def create_my_resource(name: str, kind: str, **kwargs):
        # Create and return resource instance
        return MyResource(name=name, kind=kind, **kwargs)

    register_resource("my_resource", "custom", create_my_resource, {
        "description": "My custom resource"
    })
    ```

    Args:
        name: Name for the resource type
        kind: Kind identifier for the resource
        factory_func: Function that creates resource instances
        metadata: Optional metadata about the resource
    """
    integrator = get_resource_integrator()
    integrator.register_user_resource(name, kind, factory_func=factory_func, metadata=metadata)
    print(f"Registered resource type '{name}' with kind '{kind}'")


def register_resource_class(blueprint_class: type, metadata: Dict[str, Any] = None):
    """
    Register a resource blueprint class.

    This is useful when you have a Python class that extends BaseResource:

    ```python
    from dana.core.resource import BaseResource
    from dana.core.resource.resource_helpers import register_resource_class

    class MyCustomResource(BaseResource):
        kind = "custom"

        def query(self, request):
            return f"Response: {request}"

    register_resource_class(MyCustomResource, {"description": "Custom resource"})
    ```

    Args:
        blueprint_class: Class that extends BaseResource
        metadata: Optional metadata about the resource
    """
    if not issubclass(blueprint_class, BaseResource):
        raise ValueError("blueprint_class must extend BaseResource")

    kind = getattr(blueprint_class, "kind", blueprint_class.__name__.lower())
    name = blueprint_class.__name__

    integrator = get_resource_integrator()
    integrator.register_user_resource(name, kind, blueprint_class=blueprint_class, metadata=metadata)
    print(f"Registered resource class '{name}' with kind '{kind}'")


def add_resource_search_path(path: str):
    """
    Add a directory to search for resource plugins.

    This allows Dana code to add custom directories where resources are stored:

    ```dana
    from dana.core.resource.resource_helpers import add_resource_search_path

    # Add a custom resource directory
    add_resource_search_path("/my/project/resources")
    ```

    Args:
        path: Directory path to search for resources
    """
    integrator = get_resource_integrator()
    path_obj = Path(path)

    if not path_obj.exists():
        print(f"Warning: Path does not exist: {path}")
        return

    integrator.loader.add_search_path(path_obj)
    print(f"Added resource search path: {path}")


def reload_resources():
    """
    Reload all resource plugins from disk.

    This is useful during development to pick up changes to resource files:

    ```dana
    from dana.core.resource.resource_helpers import reload_resources

    # Reload to pick up changes
    reload_resources()
    ```
    """
    integrator = get_resource_integrator()
    integrator.reload_resources()
    print("Resources reloaded")


def list_available_resources() -> Dict[str, Any]:
    """
    List all available resource types.

    Returns a dictionary with information about registered resources:

    ```dana
    from dana.core.resource.resource_helpers import list_available_resources

    resources = list_available_resources()
    for kind, info in resources.items():
        print(f"Resource: {kind} - {info.get('description', 'No description')}")
    ```

    Returns:
        Dictionary mapping resource kinds to their metadata
    """
    integrator = get_resource_integrator()
    resources = {}

    for plugin in integrator.loader.list_plugins():
        resources[plugin.kind] = {"name": plugin.name, "source": plugin.source, "path": plugin.path, "metadata": plugin.metadata}

    return resources


def get_resource_stats() -> Dict[str, Any]:
    """
    Get statistics about the resource system.

    Returns information about loaded resources, active instances, etc:

    ```dana
    from dana.core.resource.resource_helpers import get_resource_stats

    stats = get_resource_stats()
    print(f"Total plugins: {stats['plugins']}")
    print(f"Active resources: {stats['total_resources']}")
    ```

    Returns:
        Dictionary with resource system statistics
    """
    integrator = get_resource_integrator()
    return integrator.get_statistics()


# Convenience function for Dana code
def create_resource_factory(resource_class: type) -> Callable:
    """
    Create a factory function from a resource class.

    This is a helper for converting Python classes to factory functions:

    ```python
    from dana.core.resource.resource_helpers import create_resource_factory

    class MyResource(BaseResource):
        kind = "my_resource"

    factory = create_resource_factory(MyResource)
    register_resource("my_resource", "my_resource", factory)
    ```

    Args:
        resource_class: Class that extends BaseResource

    Returns:
        Factory function that creates instances of the class
    """

    def factory(name: str, kind: str, **kwargs):
        return resource_class(name=name, kind=kind, **kwargs)

    return factory
