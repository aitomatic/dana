"""Factory for creating DXA resources."""

from typing import Dict, Any
from . import BaseResource, LLMResource

class ResourceFactory:
    """Creates and configures DXA resources."""

    RESOURCE_TYPES = {
        "none": BaseResource,
        "llm": LLMResource,
    }

    @classmethod
    def create_resource(cls, config: Dict[str, Any]) -> BaseResource:
        """Create a resource with the given configuration."""
        resource_type = config.get("type", "none")
        if resource_type not in cls.RESOURCE_TYPES:
            raise ValueError(f"Unknown resource type: {resource_type}")
        return cls.RESOURCE_TYPES[resource_type](**config) 
    
    @classmethod
    def create_llm_resource(cls, config: Dict[str, Any]) -> LLMResource:
        """Create a LLM resource with the given configuration."""
        return LLMResource(**config)
    