"""
Clean LLM Resource - ResourceInstance version

Goes directly to dana.common.sys_resource.llm.legacy_llm_resource.LLMResource
following the RAGResource pattern.
"""

from typing import Any


def get_llm_resource_type():
    """Get the LLM ResourceType definition."""
    from dana.core.resource.resource_instance import ResourceType

    return ResourceType(
        name="LLMResource",
        fields={
            "name": "str",
            "model": "str",
            "temperature": "float",
            "max_tokens": "int",
            "provider": "str",
            "api_key": "str",
            "endpoint": "str",
            "timeout": "int",
        },
        field_order=["name", "model", "temperature", "max_tokens", "provider", "api_key", "endpoint", "timeout"],
        field_defaults={
            "model": "openai:gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
            "provider": "openai",
            "api_key": "",
            "endpoint": "",
            "timeout": 60,
        },
        field_comments={},
    )


class LLMSysResourceBackend:
    """Backend adapter that connects ResourceInstance to sys_resource.LLMResource."""

    def __init__(self, resource_instance: Any):
        """Initialize the backend with ResourceInstance values."""
        self.resource_instance = resource_instance
        self._sys_llm: Any = None

    async def initialize(self) -> None:
        """Initialize the underlying LLM system resource."""
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource

        # Extract values from ResourceInstance
        self._sys_llm = LegacyLLMResource(
            name=self.resource_instance.name,
            model=getattr(self.resource_instance, "model", "openai:gpt-4o-mini"),
            temperature=getattr(self.resource_instance, "temperature", 0.7),
            max_tokens=getattr(self.resource_instance, "max_tokens", 1000),
            provider=getattr(self.resource_instance, "provider", "openai"),
            api_key=getattr(self.resource_instance, "api_key", ""),
            endpoint=getattr(self.resource_instance, "endpoint", ""),
            timeout=getattr(self.resource_instance, "timeout", 60),
        )

        # Initialize the sys resource
        await self._sys_llm.initialize()

    async def cleanup(self) -> None:
        """Clean up the LLM system resource."""
        if self._sys_llm:
            await self._sys_llm.cleanup()
            self._sys_llm = None

    async def complete(self, prompt: str, **kwargs) -> Any:
        """Complete text using the LLM."""
        if not self._sys_llm:
            raise RuntimeError("LLM resource not initialized")
        return await self._sys_llm.complete(prompt, **kwargs)

    async def chat(self, messages: list, **kwargs) -> Any:
        """Chat with the LLM."""
        if not self._sys_llm:
            raise RuntimeError("LLM resource not initialized")
        return await self._sys_llm.chat(messages, **kwargs)

    async def embed(self, text: str, **kwargs) -> Any:
        """Generate embeddings."""
        if not self._sys_llm:
            raise RuntimeError("LLM resource not initialized")
        return await self._sys_llm.embed(text, **kwargs)

    def get_stats(self) -> dict[str, Any]:
        """Get LLM statistics."""
        if not self._sys_llm:
            return {"error": "LLM resource not initialized"}
        return self._sys_llm.get_stats()

    def __getattr__(self, name: str) -> Any:
        """Delegate all other operations to the sys resource."""
        if self._sys_llm:
            return getattr(self._sys_llm, name)
        raise AttributeError(f"LLM resource not initialized, cannot access '{name}'")


def create_llm_resource(**kwargs):
    """Create a clean LLM ResourceInstance with direct sys_resource backend.

    This is the modern, clean way to create LLM resources.
    No BaseResource dependency - goes directly to dana.common.sys_resource.
    """
    from dana.core.resource.resource_factory import create_resource_instance

    # Get the ResourceType
    llm_resource_type = get_llm_resource_type()

    # Create the ResourceInstance
    instance = create_resource_instance(llm_resource_type, kwargs)

    # Attach the clean sys_resource backend
    backend = LLMSysResourceBackend(instance)
    instance.set_backend(backend)

    return instance


# For registration with resource factory
def register_clean_llm_resource():
    """Register the clean LLM resource type with the factory."""
    from dana.core.resource.resource_factory import register_resource_type

    llm_resource_type = get_llm_resource_type()

    # Register with factory using clean backend
    register_resource_type(llm_resource_type, backend_factory=lambda instance, config: LLMSysResourceBackend(instance))


# Export for backward compatibility
def LLMResource(**kwargs):
    """Create LLM resource (backward compatibility function name)."""
    return create_llm_resource(**kwargs)
