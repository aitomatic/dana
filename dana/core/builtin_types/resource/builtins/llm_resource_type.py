"""
LLM Resource Type

This module provides LLMResourceType, which defines the structure and instantiation
logic for LLM resources in the core resource system.
"""

from typing import TYPE_CHECKING, Any

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.builtin_types.resource.resource_type import ResourceType

if TYPE_CHECKING:
    from dana.core.builtin_types.resource.builtins.llm_resource_instance import LLMResourceInstance


class LLMResourceType(ResourceType):
    """
    Resource type definition for LLM resources.

    This class defines the structure and instantiation logic for LLM resources,
    following the proper ResourceType -> ResourceInstance pattern.
    """

    def __init__(self):
        """Initialize the LLM resource type definition."""
        super().__init__(
            name="LLMResource",
            fields={
                "name": "str",
                "model": "str",
                "state": "str",
                "provider": "str",
                "temperature": "float",
                "max_tokens": "int",
            },
            field_order=["name", "model", "state", "provider", "temperature", "max_tokens"],
            field_defaults={
                "name": "system_llm",
                "model": "",
                "state": "READY",
                "provider": "auto",
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            field_comments={
                "name": "Name of the LLM resource instance",
                "model": "Model identifier (e.g., 'openai:gpt-4o')",
                "state": "Current state of the resource (READY, INITIALIZED, etc.)",
                "provider": "LLM provider (auto, openai, anthropic, etc.)",
                "temperature": "Sampling temperature for LLM responses",
                "max_tokens": "Maximum tokens in LLM responses",
            },
            docstring="LLM Resource type for language model interaction",
        )

    @classmethod
    def create_instance(cls, llm_resource: "LegacyLLMResource", values: dict[str, Any] | None = None) -> "LLMResourceInstance":
        """
        Create a LLMResourceInstance from an LLMResource.

        Args:
            llm_resource: The underlying LLMResource to wrap
            values: Additional field values to override defaults

        Returns:
            A new LLMResourceInstance wrapping the LLMResource
        """
        from dana.core.builtin_types.resource.builtins.llm_resource_instance import LLMResourceInstance

        # Extract values from the LLMResource
        resource_values = {
            "name": llm_resource.name,
            "model": llm_resource.model or "auto",
            "state": "READY",
            "provider": cls._extract_provider_from_model(llm_resource.model),
            "temperature": getattr(llm_resource, "temperature", 0.7),
            "max_tokens": getattr(llm_resource, "max_tokens", 2048),
        }

        # Override with any provided values
        if values:
            resource_values.update(values)

        return LLMResourceInstance(cls(), llm_resource, resource_values)

    @classmethod
    def create_instance_from_values(cls, values: dict[str, Any]) -> "LLMResourceInstance":
        """
        Create a LLMResourceInstance from field values by instantiating an LLMResource.

        Args:
            values: Field values including model, name, etc.

        Returns:
            A new LLMResourceInstance with a newly created LLMResource
        """
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
        from dana.core.builtin_types.resource.builtins.llm_resource_instance import LLMResourceInstance

        # Extract LLMResource constructor arguments
        name = values.get("name", "system_llm")
        model = values.get("model")
        temperature = values.get("temperature", 0.7)
        max_tokens = values.get("max_tokens", 2048)

        # Create the underlying LLMResource
        llm_resource = LegacyLLMResource(name=name, model=model, temperature=temperature, max_tokens=max_tokens)

        return LLMResourceInstance(LLMResourceType(), llm_resource, values)

    @classmethod
    def _extract_provider_from_model(cls, model: str | None) -> str:
        """Extract provider name from model string."""
        if not model:
            return "auto"
        if ":" in model:
            return model.split(":", 1)[0]
        return "auto"

    @classmethod
    def register(cls) -> "LLMResourceType":
        """
        Register this resource type in the global registry.

        Returns:
            The registered LLMResourceType instance
        """
        from dana.core.builtin_types.resource.resource_registry import ResourceTypeRegistry

        instance = cls()
        ResourceTypeRegistry.register_resource_type(instance)
        return instance

    @classmethod
    def create_default_instance(cls) -> "LLMResourceInstance":
        """Create a default LLMResourceInstance."""
        llm_resource_instance = cls.create_instance(LegacyLLMResource())
        return llm_resource_instance
