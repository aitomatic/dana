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
    from dana.frameworks.agent.deprecated.capability.domain_expertise import DomainExpertise

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

from typing import Any, ClassVar

# First-party imports
from dana.common.io import IOFactory
from dana.common.mixins import ToolCallable
from dana.common.resource import BaseResource
from dana.common.types import BaseRequest, BaseResponse

# Local imports
from dana.frameworks.agent.deprecated.capability.domain_expertise import DomainExpertise


class ExpertResponse(BaseResponse):
    """Expert-specific response extending base response."""

    usage: dict[str, int] | None = None
    model: str | None = None


class ExpertResource(BaseResource):
    """Resource for interacting with human experts."""

    # Class-level default configuration
    default_config: ClassVar[dict[str, Any]] = {"expertise": None, "confidence_threshold": 0.7, "system_prompt": None, "llm_config": {}}

    def __init__(
        self,
        name: str,
        expertise: DomainExpertise | None = None,
        system_prompt: str | None = None,
        confidence_threshold: float = 0.7,
        llm_config: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
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
    def expertise(self) -> DomainExpertise | None:
        """Get the domain expertise."""
        return self.config.get("expertise")

    @property
    def confidence_threshold(self) -> float:
        """Get the confidence threshold."""
        return float(self.config.get("confidence_threshold", 0.7))

    @property
    def system_prompt(self) -> str | None:
        """Get the system prompt."""
        return self.config.get("system_prompt")

    @property
    def llm_config(self) -> dict[str, Any]:
        """Get the LLM configuration."""
        return self.config.get("llm_config", {})

    async def initialize(self) -> None:
        """Initialize IO for expert interaction."""
        self._io = IOFactory.create_io("console")  # Sync creation
        await self._io.initialize()  # Async init

    @ToolCallable.tool
    async def query(self, request: BaseRequest | None = None) -> BaseResponse:
        """Get expert input."""
        if not self._io:
            await self.initialize()

        # Ensure we pass a proper BaseRequest with prompt
        if request is None:
            from dana.common.types import BaseRequest

            request = BaseRequest(arguments={"prompt": ""})
        else:
            # Ensure the request has a prompt argument
            if not hasattr(request, "arguments") or "prompt" not in request.arguments:
                from dana.common.types import BaseRequest

                request = BaseRequest(arguments={"prompt": str(request)})

        response = await self._io.query(request)
        return response

    async def cleanup(self) -> None:
        """Cleanup IO."""
        if self._io:
            await self._io.cleanup()

    def can_handle(self, request: dict[str, Any]) -> bool:
        """Check if request needs expert input."""
        return "prompt" in request
