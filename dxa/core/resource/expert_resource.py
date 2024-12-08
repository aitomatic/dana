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
    LLMError
)
from dxa.core.capability.domain_expertise import DomainExpertise
from dxa.core.resource.base_resource import ResourceConfig, ResourceResponse, BaseResource
from openai import AsyncOpenAI


@dataclass
class ExpertConfig(ResourceConfig):
    """Expert-specific configuration extending base config."""
    expertise: DomainExpertise
    api_key: str
    model: str
    system_prompt: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    confidence_threshold: float = 0.7


@dataclass
class ExpertResponse(ResourceResponse):
    """Expert-specific response extending base response."""
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class ExpertResource(BaseResource):
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
        self._client = None

    async def initialize(self) -> None:
        """Initialize the expert resource."""
        self._client = AsyncOpenAI(api_key=self.config.api_key)
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the expert resource."""
        if self._client:
            await self._client.close()
        self._client = None
        self._is_available = False

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request matches expertise domain."""
        if not isinstance(request, dict) or "prompt" not in request:
            return False
            
        prompt = request["prompt"]
        expertise = self.config.expertise
        
        # Check for required context
        has_requirements = all(req in prompt.lower() for req in expertise.requirements)
        
        # Check for relevant keywords
        has_keywords = any(keyword in prompt.lower() for keyword in expertise.keywords)
        
        return has_requirements and has_keywords

    async def query(self, request: Dict[str, Any]) -> ExpertResponse:
        """Query with domain expertise context."""
        if not self.can_handle(request):
            raise LLMError(f"Request cannot be handled by {self.config.expertise.name} expert")

        enhanced_request = {
            **request,
            "prompt": self._enhance_prompt(request["prompt"])
        }

        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": enhanced_request["prompt"]}],
                **enhanced_request.get("parameters", {})
            )
            
            return ExpertResponse(
                content=response.choices[0].message.content,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                } if hasattr(response, 'usage') else None,
                model=response.model
            )
        except Exception as e:
            raise LLMError(f"Expert query failed: {str(e)}") from e

    def _enhance_prompt(self, prompt: str) -> str:
        """Add domain context to prompt."""
        return f"""As an expert in {self.config.expertise.name}, 
        with capabilities in: {', '.join(self.config.expertise.capabilities)}
        
        Please address this query: {prompt}""" 