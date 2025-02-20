"""Factory for creating DXA resources."""

from typing import Dict, Any, Optional
from .base_resource import BaseResource
from .llm_resource import LLMResource
from .expert_resource import ExpertResource

class ResourceFactory:
    """Creates resources based on type."""
    
    @classmethod
    def create_resource(cls, resource_type: str, config: Dict[str, Any]) -> BaseResource:
        """Create resource instance."""
        if resource_type == "llm":
            return LLMResource(name=config.get("name", "llm"), config=config)
        if resource_type == "expert":
            return ExpertResource(name=config.get("name", "expert"))
        raise ValueError(f"Unknown resource type: {resource_type}")
    
    @classmethod
    def create_llm_resource(cls, config: Optional[Dict[str, Any]] = None, system_prompt: Optional[str] = None) -> LLMResource:
        """Create a LLM resource with the given configuration."""
        return LLMResource(name=config.get("name", "llm"), config=config, system_prompt=system_prompt)

    