"""Base agent implementation."""

from abc import ABC
from typing import Dict, Any, Optional
import logging
from dxa.core.resources.base import BaseResource
from dxa.agents.agent_llm import AgentLLM
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resources.expert import ExpertResource

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        reasoning: BaseReasoning,
        internal_llm_config: Dict[str, Any],
        resources: Optional[Dict[str, BaseResource]] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize base agent."""
        self.name = name
        self.description = description or f"Agent: {name}"
        self.logger = logging.getLogger(f"Agent:{name}")
        
        # Initialize agent's LLM
        self.llm = AgentLLM(
            name=f"{name}_llm",
            config=internal_llm_config,
            system_prompt=system_prompt
        )
        
        # Set up resources
        self.resources = resources or {}
        
        # Set up reasoning with agent's LLM
        self.reasoning = reasoning
        self.reasoning.set_llm(self.llm)  # Pass the actual LLM resource

    async def initialize(self) -> None:
        """Initialize agent and resources."""
        # Initialize agent's LLM first
        await self.llm.initialize()
        
        # Initialize other resources
        for resource in self.resources.values():
            await resource.initialize()
            
        self.logger.info(
            "Agent initialized with resources: %s",
            list(self.resources.keys())
        )

    async def cleanup(self) -> None:
        """Clean up agent and resources."""
        # Clean up resources
        for resource in self.resources.values():
            await resource.cleanup()
            
        # Clean up agent's LLM
        await self.llm.cleanup()
        
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