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
    from opendxa.agent.capability.domain_expertise import DomainExpertise

    expertise = DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"]
    )

    expert = ExpertResource(
        name="math_expert",
        config={
            "expertise": expertise,
            "model": "gpt-4",
            "confidence_threshold": 0.7
        }
    )

    response = await expert.query({
        "prompt": "Solve the equation x^2 + 2x + 1 = 0"
    })
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, ClassVar
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse
from opendxa.agent.capability.domain_expertise import DomainExpertise
from opendxa.common.io import IOFactory


@dataclass
class ExpertResponse(ResourceResponse):
    """Expert-specific response extending base response."""
    content: str = ""
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class ExpertResource(BaseResource):
    """Resource for interacting with human experts."""

    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "expertise": None,
        "confidence_threshold": 0.7,
        "system_prompt": None,
        "llm_config": {}
    }

    def __init__(
        self,
        name: str,
        expertise: Optional[DomainExpertise] = None,
        system_prompt: Optional[str] = None,
        confidence_threshold: float = 0.7,
        llm_config: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize expert resource.

        Args:
            name: Resource name
            expertise: Optional domain expertise
            system_prompt: Optional system prompt
            confidence_threshold: Confidence threshold for responses
            llm_config: Optional LLM configuration
            config: Optional additional configuration
        """
        # Build config dict from parameters
        config_dict = config or {}
        if expertise:
            config_dict["expertise"] = expertise
        if system_prompt:
            config_dict["system_prompt"] = system_prompt
        if confidence_threshold != 0.7:
            config_dict["confidence_threshold"] = confidence_threshold
        if llm_config:
            config_dict["llm_config"] = llm_config

        super().__init__(name=name, config=config_dict)
        self._io = IOFactory.create_io("console")

    @property
    def expertise(self) -> Optional[DomainExpertise]:
        """Get the domain expertise."""
        return self.config.get("expertise")

    @property
    def confidence_threshold(self) -> float:
        """Get the confidence threshold."""
        return float(self.config.get("confidence_threshold", 0.7))

    @property
    def system_prompt(self) -> Optional[str]:
        """Get the system prompt."""
        return self.config.get("system_prompt")

    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get the LLM configuration."""
        return self.config.get("llm_config", {})

    async def initialize(self) -> None:
        """Initialize IO for expert interaction."""
        self._io = IOFactory.create_io("console")  # Sync creation
        await self._io.initialize()  # Async init

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Get expert input."""
        if not self._io:
            await self.initialize()

        # Ensure we pass a proper dictionary with prompt
        prompt = request.get("prompt") or ""
        response = await self._io.query({"prompt": prompt})
        return response

    async def cleanup(self) -> None:
        """Cleanup IO."""
        if self._io:
            await self._io.cleanup()

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request needs expert input."""
        return "prompt" in request