"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from dxa.core.resources.llm import LLMResource
from dxa.core.reasoning.base import BaseReasoning

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize base agent.
        
        Args:
            name: Name of this agent
            llm_config: Configuration for the agent's LLM
            reasoning: Reasoning pattern to use
            system_prompt: Optional system prompt for the LLM
            description: Optional description of this agent
        """
        self.name = name
        self.description = description or f"Agent: {name}"
        self.logger = logging.getLogger(f"Agent:{name}")
        
        # Initialize LLM
        self.llm = LLMResource(
            name=f"{name}_llm",
            llm_config=llm_config,
            system_prompt=system_prompt
        )
        
        # Set up reasoning
        self.reasoning = reasoning
        self.reasoning.set_llm_fn(self.llm.query)
        
        # Initialize state
        self.state: Dict[str, Any] = {}
        self._is_running = False

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await self.llm.initialize()
        self._is_running = True
        self.logger.info("Agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.llm.cleanup()
        self._is_running = False
        self.logger.info("Agent cleaned up")

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main loop.
        
        Args:
            context: Initial context for the agent
            
        Returns:
            Dict containing results of agent's operation
        """
        pass

    async def handle_error(self, error: Exception) -> None:
        """Handle errors during agent operation.
        
        Args:
            error: The error that occurred
        """
        self.logger.error("Error during agent operation: %s", str(error))
        await self.cleanup()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 