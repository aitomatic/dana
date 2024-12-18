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
from dxa.core.resource.base_resource import BaseResource, ResourceResponse, ResourceConfig


@dataclass
class ExpertConfig(ResourceConfig):
    """Expert-specific configuration."""
    expertise: DomainExpertise = None
    confidence_threshold: float = 0.7
    llm_config: LLMConfig = None


@dataclass
class ExpertResponse(ResourceResponse):
    """Expert-specific response extending base response."""
    content: str = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class ExpertResource(BaseResource):
    """Expert resource that uses an LLM for domain-specific queries."""
    
    def __init__(
        self,
        name: str,
        config: Union[Dict[str, Any], ExpertConfig],
        description: Optional[str] = None
    ):
        """Initialize expert resource."""
        if isinstance(config, dict):
            config = ExpertConfig.from_dict(config)
        
        if not config.expertise:
            raise ValueError("ExpertResource requires expertise configuration")
            
        if not config.llm_config:
            raise ValueError("ExpertResource requires LLM configuration")
            
        super().__init__(name=name, resource_config=config)
        self._llm = LLMResource(name=f"{name}_llm", config=config.llm_config)

    async def initialize(self) -> None:
        """Initialize the expert and its LLM."""
        await self._llm.initialize()
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the expert and its LLM."""
        await self._llm.cleanup()
        self._is_available = False

    async def query(self, request: Dict[str, Any]) -> ExpertResponse:
        """Query with domain expertise context."""
        if not self.can_handle(request):
            raise LLMError(f"Request cannot be handled by {self.config.expertise.name} expert")

        # Enhance the prompt with domain context
        enhanced_request = request.copy()
        enhanced_request["prompt"] = self._enhance_prompt(request["prompt"])

        # Get response using expert's domain logic
        expert_response = await self._process_expert_query(enhanced_request)
        return expert_response

    async def _process_expert_query(self, request: Dict[str, Any]) -> ExpertResponse:
        """Process the query using expert's domain logic.
        
        Default implementation uses the LLM directly. Subclasses can override
        to add domain-specific processing.
        """
        if self._llm and self._llm.is_available:
            llm_response = await self._llm.query(request)
            return ExpertResponse(
                success=llm_response.success,
                error=llm_response.error,
                content=llm_response.content,
                usage=llm_response.usage,
                model=llm_response.model
            )
        else:
            return ExpertResponse(
                success=True,
                error=False,
                content='Default Expert Response'
            )

    def _enhance_prompt(self, prompt: str) -> str:
        """Add domain context to prompt."""
        return f"""As an expert in {self.config.expertise.name}, 
        with capabilities in: {', '.join(self.config.expertise.capabilities)}
        
        Please address this query: {prompt}""" 

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the request can be handled by this expert.
        
        Args:
            request: The incoming request
            
        Returns:
            bool: True if the request matches expert's domain
        """
        if not request.get("prompt"):
            return False
        
        # Check if request contains any expertise keywords
        prompt = request["prompt"].lower()
        return any(keyword.lower() in prompt
                   for keyword in self.config.expertise.keywords)