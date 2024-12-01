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
from typing import Dict, Any, Optional
from dxa.core.resource.llm_resource import (
    LLMResponse, 
    LLMResource,
    LLMError
)
from dxa.core.capability.domain_expertise import DomainExpertise


@dataclass
class ExpertConfig:
    """Expert-specific configuration extending LLM config."""
    expertise: DomainExpertise
    api_key: str
    model: str
    system_prompt: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    confidence_threshold: float = 0.7


class ExpertResource(LLMResource[ExpertConfig, LLMResponse]):
    """Expert resource with specialized config."""
    
    def __init__(
        self,
        name: str,
        config: ExpertConfig,
        description: Optional[str] = None
    ):
        """Initialize expert resource."""
        super().__init__(
            name=name,
            config=config,
            description=description or f"Expert in {config.expertise.name}"
        )

    async def query(self, request: Dict[str, Any]) -> LLMResponse:
        """Query with domain expertise context."""
        if not self.can_handle(request):
            raise LLMError(f"Request cannot be handled by {self.config.expertise.name} expert")

        enhanced_request = {
            **request,
            "prompt": self._enhance_prompt(request["prompt"])
        }

        return await super().query(enhanced_request)

    def _enhance_prompt(self, prompt: str) -> str:
        """Add domain context to prompt."""
        return f"""As an expert in {self.config.expertise.name}, 
        with capabilities in: {', '.join(self.config.expertise.capabilities)}
        
        Please address this query: {prompt}""" 