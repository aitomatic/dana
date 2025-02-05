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
from .llm_resource import LLMConfig
from ..capability.domain_expertise import DomainExpertise
from .base_resource import BaseResource, ResourceResponse, ResourceConfig
from ..io import IOFactory


@dataclass
class ExpertConfig(ResourceConfig):
    """Expert-specific configuration."""
    expertise: Optional[DomainExpertise] = None
    confidence_threshold: float = 0.7
    llm_config: Optional[LLMConfig] = None


@dataclass
class ExpertResponse(ResourceResponse):
    """Expert-specific response extending base response."""
    content: str = ""
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class ExpertResource(BaseResource):
    """Resource for interacting with human experts."""

    # pylint: disable=too-many-arguments
    def __init__(self,
                 name: str,
                 expertise: Optional[DomainExpertise] = None,
                 system_prompt: Optional[str] = None,
                 confidence_threshold: float = 0.7,
                 llm_config: Optional[LLMConfig] = None):
        super().__init__(name)
        self.expertise = expertise
        self.system_prompt = system_prompt
        self.confidence_threshold = confidence_threshold
        self.llm_config = llm_config
        self._io = IOFactory.create_io("console")

    async def initialize(self) -> None:
        """Initialize IO for expert interaction."""
        self._io = IOFactory.create_io("console")  # Sync creation
        await self._io.initialize()  # Async init

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get expert input."""
        if not self._io:
            await self.initialize()

        # Ensure we pass a proper dictionary with prompt
        prompt = request.get("prompt") or ""
        response = await self._io.query({"prompt": prompt})
        return {
            "success": True,
            "content": response
        }

    async def cleanup(self) -> None:
        """Cleanup IO."""
        if self._io:
            await self._io.cleanup()

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request needs expert input."""
        return "prompt" in request