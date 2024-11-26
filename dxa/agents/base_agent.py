"""Base agent implementation."""

from abc import ABC
from typing import Dict, Any, Optional
import logging
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resources.base_resource import BaseResource
from dxa.core.resources.expert import ExpertResource
from dxa.agents.agent_llm import AgentLLM

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        reasoning: BaseReasoning,
        llm_config: Dict[str, Any],
        resources: Optional[Dict[str, BaseResource]] = None,
        agent_prompts: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ):
        """Initialize base agent."""
        self.name = name
        self.description = description or f"Agent: {name}"
        self.logger = logging.getLogger(f"Agent:{name}")
        
        # Set up resources
        self.resources = resources or {}
        
        # Set up agent's LLM
        self.agent_llm = AgentLLM(
            name=f"{name}_llm",
            agent_prompts=agent_prompts,
            config=llm_config
        )
        
        # Set up reasoning with agent's LLM
        reasoning.set_agent_llm(self.agent_llm)
        reasoning.set_available_resources(self.resources)
        self.reasoning = reasoning

        # Initialize running state
        self._is_running = True

    async def initialize(self) -> None:
        """Initialize agent and resources."""
        # Initialize agent's LLM first
        await self.agent_llm.initialize()
        await self.reasoning.initialize()

        # Initialize other resources
        for resource in self.resources.values():
            if callable(getattr(resource, "initialize", None)):
                await resource.initialize()
            
        self.logger.info(
            "Agent initialized with resources: %s",
            list(self.resources.keys())
        )

    async def cleanup(self) -> None:
        """Clean up agent and resources."""
        # Clean up resources
        for resource in self.resources.values():
            if callable(getattr(resource, "cleanup", None)):
                await resource.cleanup()
        
        await self.reasoning.cleanup()
        await self.agent_llm.cleanup()
        
        self.logger.info("Agent cleaned up") 

    async def use_expert(self, domain: str, request: str) -> str:
        """Use expert for specialized domain knowledge.
        
        Args:
            domain: The domain of expertise needed
            request: The specific request for the expert
            
        Returns:
            Expert's response as a string
            
        Raises:
            ValueError: If no expert is found for the given domain
        """
        experts: Dict[str, ExpertResource] = self.resources.get_by_type(ExpertResource)
        expert = next(
            (e for e in experts.values() if e.expertise.name.lower() == domain.lower()),
            None
        )
        
        if not expert:
            raise ValueError(f"No expert found for domain: {domain}")
            
        response = await expert.query({"prompt": request})
        return response["response"]
    
    def get_system_prompt(self) -> str:
        """Get the default system prompt for the agent that will go
        before the reasoning system prompt. Defaults to empty string."""

        return ""
    
    # pylint: disable=unused-argument
    def get_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the default prompt for the agent that will go
        before the reasoning prompt. Defaults to empty string."""
        return ""

    async def query_llm(self, llm_request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the agent's LLM.
        
        Args:
            llm_request: Dictionary containing the LLM request parameters
            including system_prompt and prompt, temperature, and max_tokens, etc.
        
        Returns:
            Dictionary containing the LLM response
        """
        messages = []
        if "system_prompt" in llm_request:
            messages.append({"role": "system", "content": llm_request["system_prompt"]})
        if "prompt" in llm_request:
            messages.append({"role": "user", "content": llm_request["prompt"]})

        return await self.agent_llm.query(
            messages, 
            **{k: v for k, v in llm_request.items() if k not in ["system_prompt", "prompt"]}
        )

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the agent, which will run the reasoning loop."""
        return await self.reasoning.reason(request)
