"""Base reasoning pattern for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass
import logging
from dxa.agents.state import StateManager
from dxa.core.resources.base import BaseResource
from dxa.core.resources.expert import ExpertResource
from dxa.core.resources.human import HumanUserResource
from dxa.agents.agent_llm import AgentLLM
if TYPE_CHECKING:
    from dxa.agents.agent_llm import BaseLLM

class ReasoningStatus(str, Enum):
    """Possible statuses from reasoning."""
    NEED_EXPERT = "NEED_EXPERT"
    NEED_INFO = "NEED_INFO"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

@dataclass
class ReasoningResult:
    """Standard structure for reasoning results."""
    # Core fields
    status: ReasoningStatus
    steps: list[str]
    
    # For NEED_EXPERT
    expert_domain: Optional[str] = None
    expert_request: Optional[Dict[str, Any]] = None
    expert_context: Optional[str] = None
    
    # For NEED_INFO
    user_prompt: Optional[str] = None
    user_context: Optional[str] = None
    expected_format: Optional[str] = None
    
    # For COMPLETE
    final_answer: Optional[str] = None
    explanation: Optional[str] = None
    
    # For ERROR
    reason: Optional[str] = None
    suggestion: Optional[str] = None
    
    # For all
    raw_content: Optional[str] = None

class BaseReasoning(ABC):
    """Base class for reasoning patterns."""
    
    def __init__(self):
        """Initialize base reasoning."""
        self.llm = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_manager = StateManager(agent_name=self.__class__.__name__)
        self.available_resources: Dict[str, BaseResource] = {}

    async def initialize(self) -> None:
        """Initialize the reasoning pattern."""
        if not self.llm:
            raise ValueError("LLM must be set before initialization")
        # ... rest of initialization ...

    def set_available_resources(self, resources: Dict[str, BaseResource]) -> None:
        """Inform reasoning about available resources."""
        self.available_resources = resources
        
        # Log available resources by type
        experts = [r for r in resources.values() if isinstance(r, ExpertResource)]
        humans = [r for r in resources.values() if isinstance(r, HumanUserResource)]
        others = [
            r for r in resources.values()
            if not isinstance(r, (ExpertResource, HumanUserResource))
        ]
        
        if experts:
            self.logger.info(
                "Available experts: %s",
                [f"{e.expertise.name} ({e.expertise.description})" for e in experts]
            )
        if humans:
            self.logger.info(
                "Available human users: %s",
                [f"{h.name} ({h.role})" for h in humans]
            )
        if others:
            self.logger.info(
                "Other available resources: %s",
                [f"{r.name} ({r.description})" for r in others]
            )

    def get_resource_description(self) -> str:
        """Get formatted description of all available resources."""
        description = []
        
        # Group resources by type
        experts = [
            r for r in self.available_resources.values()
            if isinstance(r, ExpertResource)
        ]
        humans = [
            r for r in self.available_resources.values()
            if isinstance(r, HumanUserResource)
        ]
        others = [
            r for r in self.available_resources.values()
            if not isinstance(r, (ExpertResource, HumanUserResource))
        ]
        
        # Add expert descriptions
        if experts:
            description.append("Available Domain Experts:")
            for expert in experts:
                description.extend([
                    f"- {expert.expertise.name}:",
                    f"  Description: {expert.expertise.description}",
                    f"  Capabilities: {', '.join(expert.expertise.capabilities)}",
                    f"  Keywords: {', '.join(expert.expertise.keywords)}"
                ])
        
        # Add human user descriptions
        if humans:
            description.append("\nAvailable Human Users:")
            for human in humans:
                description.extend([
                    f"- {human.name}:",
                    f"  Role: {human.role}",
                    f"  Description: {human.description}"
                ])
        
        # Add other resource descriptions
        if others:
            description.append("\nOther Available Resources:")
            for resource in others:
                description.extend([
                    f"- {resource.name}:",
                    f"  Description: {resource.description}"
                ])
        
        return "\n".join(description)

    def has_resource(self, resource_name: str) -> bool:
        """Check if a specific resource is available."""
        return resource_name in self.available_resources

    @abstractmethod
    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> ReasoningResult:
        """Execute reasoning process."""
        pass 

    def set_llm(self, llm: 'BaseLLM') -> None:
        """Set the LLM instance for this reasoning engine.
        
        Args:
            llm: The LLM instance to use for reasoning
        """
        self.llm = llm

    async def _query_llm(self, request: Dict[str, Any]) -> Dict[str, str]:
        """Query the LLM with the given request.
        
        Args:
            request: Dictionary containing the LLM request parameters
        
        Returns:
            Dictionary containing the LLM response
        
        Raises:
            AttributeError: If LLM is not initialized
        """
        if not hasattr(self, 'llm'):
            raise AttributeError("LLM not initialized. Ensure 'llm' is set during initialization.")
        llm: AgentLLM = self.llm
        return await llm.query(
            messages=request["messages"],
            **{k: v for k, v in request.items() if k != "messages"}
        )