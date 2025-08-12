"""
Resource Factory for Dana

Creates ResourceInstance objects with appropriate backend implementations.
This replaces the complex bridge system with simple composition.
"""

from collections.abc import Callable
from typing import Any

from dana.core.resource.resource_instance import ResourceInstance, ResourceType

# Registry of backend factories for resource types
_backend_factories: dict[str, Callable[[ResourceInstance, dict[str, Any] | None], Any]] = {}


def create_resource_instance(
    resource_type: ResourceType, values: dict[str, Any] | None = None, config: dict[str, Any] | None = None
) -> ResourceInstance:
    """Create a ResourceInstance with appropriate backend.

    Args:
        resource_type: The ResourceType defining the resource structure
        values: Initial field values for the resource
        config: Additional configuration for backend creation

    Returns:
        ResourceInstance with backend attached if needed
    """
    # Create the base instance
    instance = ResourceInstance(resource_type, values)

    # Determine if this needs a backend based on resource type name
    backend = _create_backend_for_type(resource_type.name, instance, config)
    if backend:
        instance.set_backend(backend)

    return instance


def register_resource_type(
    resource_type: ResourceType, backend_factory: Callable[[ResourceInstance, dict[str, Any] | None], Any] | None = None
) -> None:
    """Register a resource type with optional backend factory.

    Args:
        resource_type: The ResourceType to register
        backend_factory: Optional factory function to create backend
    """
    if backend_factory:
        _backend_factories[resource_type.name] = backend_factory


def _create_backend_for_type(type_name: str, instance: ResourceInstance, config: dict[str, Any] | None = None) -> Any | None:
    """Create appropriate backend based on resource type.

    Args:
        type_name: Name of the resource type
        instance: The ResourceInstance to get values from
        config: Additional configuration

    Returns:
        Backend implementation or None if pure Dana resource
    """
    # Check registered factories first
    if type_name in _backend_factories:
        return _backend_factories[type_name](instance, config)

    # Normalize type name for comparison
    type_lower = type_name.lower()

    # LLM Resources
    if "llm" in type_lower or type_lower in ["languagemodel", "language_model"]:
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource

        # Extract configuration from instance fields
        model = instance.get_field("model") or config.get("model", "default") if config else "default"
        temperature = instance.get_field("temperature") or config.get("temperature", 0.7) if config else 0.7
        max_tokens = instance.get_field("max_tokens") or config.get("max_tokens", 1000) if config else 1000

        # Create the LLM backend
        return LegacyLLMResource(name=f"{type_name}_backend", model=model, temperature=temperature, max_tokens=max_tokens)

    # MCP Resources
    elif "mcp" in type_lower or type_lower in ["modelcontextprotocol", "model_context_protocol"]:
        # For now, don't create MCP backend automatically due to transport complexity
        # MCP resources need proper URL/transport configuration
        return None

    # RAG Resources - skip auto backend, they create their own
    elif "rag" in type_lower or "retrieval" in type_lower:
        # RAG resources handle their own backend creation
        return None

    # Knowledge Base Resources
    elif "knowledge" in type_lower or "kb" in type_lower:
        from dana.common.sys_resource.knowledge.knowledge_base_resource import KnowledgeBaseResource

        connection_string = instance.get_field("connection_string") or "sqlite:///knowledge.db"

        return KnowledgeBaseResource(name=f"{type_name}_backend", connection_string=connection_string)

    # Embedding Resources
    elif "embedding" in type_lower or "embed" in type_lower:
        from dana.common.sys_resource.embedding.embedding_resource import EmbeddingResource

        provider = instance.get_field("provider") or "openai"
        model = instance.get_field("model") or "text-embedding-ada-002"

        return EmbeddingResource(name=f"{type_name}_backend", provider=provider, model=model)

    # Pure Dana resources - no backend needed
    return None


def create_resource_instance_from_plugin(plugin_class: type, name: str, **kwargs) -> ResourceInstance:
    """Create a ResourceInstance from a legacy plugin class.

    This is for backward compatibility with existing BaseResource plugins.

    Args:
        plugin_class: The plugin class (used to extend BaseResource)
        name: Name for the resource
        **kwargs: Arguments for the plugin

    Returns:
        ResourceInstance wrapping the plugin as a backend
    """

    # Create a minimal ResourceType for the plugin
    resource_type = ResourceType(
        name=plugin_class.__name__.replace("Resource", ""),
        fields={"name": "str"},
        field_order=["name"],
        field_defaults={"name": name},
        field_comments={},
    )

    # Create instance
    instance = ResourceInstance(resource_type, {"name": name})

    # For plugins that extend BaseSysResource, use them directly
    # For plugins that extended BaseResource, we'll need to adapt them
    try:
        # Try to instantiate as BaseSysResource
        backend = plugin_class(name=name, **kwargs)
        instance.set_backend(backend)
    except Exception as e:
        print(f"Warning: Could not create backend for {plugin_class.__name__}: {e}")

    return instance
