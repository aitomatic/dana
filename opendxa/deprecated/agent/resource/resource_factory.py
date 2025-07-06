"""Factory for creating DXA resources."""

from typing import Any

# First-party imports
from dana.common.resource import BaseResource, LLMResource

# Local imports
from dana.frameworks.agent.resource.expert_resource import ExpertResource


class ResourceFactory:
    """Creates resources based on type."""

    @classmethod
    def create_resource(cls, resource_type: str, config: dict[str, Any]) -> BaseResource:
        """Create resource instance."""
        if resource_type == "llm":
            return LLMResource(name=config.get("name", "llm"), config=config)
        if resource_type == "expert":
            return ExpertResource(name=config.get("name", "expert"))
        raise ValueError(f"Unknown resource type: {resource_type}")

    @classmethod
    def create_llm_resource(cls, config: dict[str, Any]) -> LLMResource:
        """Create a LLM resource with the given configuration."""
        return LLMResource(**config)
