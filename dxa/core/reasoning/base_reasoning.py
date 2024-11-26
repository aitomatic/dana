"""Base reasoning pattern for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from openai.types.chat import ChatCompletion
from dxa.agents.state import StateManager
from dxa.core.resources.base_resource import BaseResource
from dxa.core.resources.expert import ExpertResource
from dxa.core.resources.human import HumanUserResource
from dxa.agents.agent_llm import AgentLLM

class DuplicateReasoningStatus(str, Enum):
    """Possible statuses from reasoning."""
    NEED_EXPERT = "NEED_EXPERT"
    NEED_INFO = "NEED_INFO"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

@dataclass
class DuplicateReasoningResult:
    """Standard structure for reasoning results."""
    status: DuplicateReasoningStatus
    steps: list[str]
    expert_domain: Optional[str] = None
    expert_request: Optional[Dict[str, Any]] = None
    user_prompt: Optional[str] = None
    final_answer: Optional[str] = None
    explanation: Optional[str] = None
    reason: Optional[str] = None
    suggestion: Optional[str] = None

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
        self.agent_llm = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_manager = StateManager(agent_name=self.__class__.__name__)
        self.available_resources: Dict[str, BaseResource] = {}
        self.current_phase: Optional[str] = "basic reasoning"

    async def initialize(self) -> None:
        """Initialize the reasoning pattern."""
        if not self.agent_llm:
            raise ValueError("Agent LLM must be set before initialization")
        # ... rest of initialization ...

    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute reasoning loop."""

        # Record the start of reasoning
        observation = {
            "context": context,
            "query": query
        }
        
        self.state_manager.add_observation(
            content=observation,
            source=self.__class__.__name__,
            metadata=f"starting {self.current_phase} phase"
        )
        
        # Get phase-specific prompt
        system_prompt = self.get_system_prompt(context, query)
        prompt = self.get_reasoning_prompt(context, query)
        
        # Format proper LLM request
        llm_request = {
            "system_prompt": system_prompt,
            "prompt": prompt,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', None)
        }
        
        try:
            # Get response from Agent LLM
            llm_response = await self._query_agent_llm(llm_request)
            response = llm_response
            if isinstance(llm_response, ChatCompletion):
                response = llm_response.choices[0].message.content
            
            self.state_manager.add_observation(
                content=response,
                source=self.__class__.__name__,
                metadata=f"ending {self.current_phase} phase"
            )
            
            return self.reason_post_process(response)
            
        except Exception as e:
            self.logger.error(
                "Error in %s phase: %s",
                self.current_phase,
                str(e)
            )
            self.state_manager.add_observation(
                content=str(e),
                source="ooda_reasoning",
                metadata={
                    "phase": self.current_phase,
                    "type": "error"
                }
            )
            raise
    
    @abstractmethod
    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Post-process the response from the LLM and return a standardized result."""

    @abstractmethod
    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the reasoning prompt."""

    # pylint: disable=unused-argument
    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the reasoning system prompt."""
        return ""

    def get_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the system prompt by combining agent and reasoning system prompts."""
        reasoning_system_prompt = self.get_reasoning_system_prompt(context, query)
        if self.agent_llm and hasattr(self.agent_llm, 'get_system_prompt'): 
            agent_system_prompt = self.agent_llm.get_system_prompt(context, query)
            return f"{agent_system_prompt}\n\n{reasoning_system_prompt}"
        else:
            return reasoning_system_prompt

    def get_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the prompt by combining agent and reasoning prompts."""
        reasoning_prompt = self.get_reasoning_prompt(context, query)
        if self.agent_llm and hasattr(self.agent_llm, 'get_prompt'):
            agent_prompt = self.agent_llm.get_prompt(context, query)
            return f"{agent_prompt}\n\n{reasoning_prompt}"
        else:
            return reasoning_prompt

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

    def set_agent_llm(self, agent_llm: AgentLLM) -> None:
        """Set the agent LLM instance for this reasoning engine.
        
        Args:
            agent_llm: The agent LLM instance to use for reasoning
        """
        self.agent_llm = agent_llm

    async def _query_agent_llm(self, llm_request: Dict[str, Any]) -> Dict[str, str]:
        """Query the agent LLM with the given request.
        
        Args:
            llm_request: Dictionary containing the LLM request parameters
            including system_prompt and prompt, temperature, and max_tokens, etc.
        
        Returns:
            Dictionary containing the LLM response
        
        Raises:
            AttributeError: If LLM is not initialized
        """
        if not hasattr(self, 'agent_llm'):
            raise AttributeError("Agent LLM not initialized. Ensure 'agent_llm' is set during initialization.")
        if not hasattr(self.agent_llm, 'query'):
            raise AttributeError("Agent LLM does not have a 'query' method.")

        messages = []
        if "system_prompt" in llm_request:
            messages.append({"role": "system", "content": llm_request["system_prompt"]})
        if "prompt" in llm_request:
            messages.append({"role": "user", "content": llm_request["prompt"]})

        return await self.agent_llm.query(messages)

    async def cleanup(self) -> None:    
        """Clean up resources used by the reasoning instance."""
        # Add any necessary cleanup logic here
        pass