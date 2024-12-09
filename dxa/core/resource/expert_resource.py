"""Expert resource implementation for DXA.

This module implements domain-expert behavior using Large Language Models (LLMs).
It combines domain expertise definitions with LLM capabilities to create
specialized agents that can handle domain-specific queries with high competency.

Classes:
    ExpertResource: LLM-powered domain expert resource

Features:
    - Domain-specific expertise configuration
    - Confidence-based query handling
    - Enhanced prompting with domain context
    - Automatic system prompt generation

Example:
    from dxa.core.capabilities.expertise import DomainExpertise
    
    expertise = DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"]
    )
    
    expert = ExpertResource(
        name="math_expert",
        expertise=expertise,
        config={"model": "gpt-4"}
    )
    
    response = await expert.query({
        "prompt": "Solve the equation x^2 + 2x + 1 = 0"
    })
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from dxa.core.resource.llm_resource import (
    LLMResource,
    LLMError,
    LLMConfig
)
from dxa.core.capability.domain_expertise import DomainExpertise
from dxa.core.resource.base_resource import ResourceResponse


@dataclass
class ExpertConfig(LLMConfig):
    """Expert-specific configuration extending LLM config."""
    expertise: DomainExpertise = None,
    confidence_threshold: float = 0.7
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ExpertConfig':
        """Create config from dictionary."""
        return cls(**{
            k: v for k, v in config_dict.items() 
            if k in cls.__dataclass_fields__
        })


@dataclass
class ExpertResponse(ResourceResponse):
    """Expert-specific response extending base response."""
    content: str = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class ExpertResource(LLMResource):
    """Expert resource with specialized config."""
    
    def __init__(
        self,
        name: str,
        config: Union[Dict[str, Any], ExpertConfig],
        description: Optional[str] = None
    ):
        """Initialize expert resource."""
        if isinstance(config, dict):
            config = ExpertConfig.from_dict(config)
        super().__init__(
            name=name,
            config=config,
            description=description or f"Expert in {config.expertise.name}"
        )

    async def query(self, request: Dict[str, Any]) -> ExpertResponse:
        """Query with domain expertise context."""
        if not self.can_handle(request):
            raise LLMError(f"Request cannot be handled by {self.config.expertise.name} expert")

        # Enhance the prompt with domain context
        enhanced_request = request.copy()
        enhanced_request["prompt"] = self._enhance_prompt(request["prompt"])

        # Use parent class's query method
        llm_response = await super().query(enhanced_request)

        # Convert LLMResponse to ExpertResponse
        return ExpertResponse(
            success=llm_response.success,
            error=llm_response.error,
            content=llm_response.content,
            usage=llm_response.usage,
            model=llm_response.model
        )

    def _enhance_prompt(self, prompt: str) -> str:
        """Add domain context to prompt."""
        return f"""As an expert in {self.config.expertise.name}, 
        with capabilities in: {', '.join(self.config.expertise.capabilities)}
        
        Please address this query: {prompt}""" 