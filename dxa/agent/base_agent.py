"""Base implementation for DXA agents.

This module provides the foundational BaseAgent class that all other agent types
inherit from. It implements core functionality like initialization, resource
management, and error handling.

Classes:
    BaseAgent: Abstract base class for all DXA agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, AsyncIterator
import logging
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningConfig
from dxa.core.resources.expert import ExpertResource
from dxa.agent.agent_llm import AgentLLM
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda import OODAReasoning
from dxa.agent.progress import AgentProgress
from dxa.common.errors import (
    ReasoningError, 
    ConfigurationError, 
    AgentError,
    ResourceError,
    DXAConnectionError
)

class BaseAgent(ABC):
    """Base class providing common agent functionality.
    
    This abstract class defines the interface and common functionality that all
    DXA agents must implement. It handles resource initialization, reasoning
    system setup, and provides helper methods for expert consultation.
    
    Attributes:
        name: Agent identifier
        mode: Operating mode ("autonomous", "interactive", etc.)
        llm: Internal LLM instance for agent processing
        reasoning: Reasoning system instance
        resources: Dictionary of available resources
        logger: Logger instance for this agent
        
    Args:
        name: Name of this agent
        config: Configuration dictionary
        mode: Operating mode (default: "autonomous")
    """
    
    # Map strategy names to reasoning classes
    REASONING_STRATEGIES: Dict[str, Type[BaseReasoning]] = {
        "ooda": OODAReasoning,
        "cot": ChainOfThoughtReasoning
    }
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        mode: str = "autonomous"
    ):
        """Initialize base agent.
        
        Args:
            name: Name of this agent
            config: Configuration dictionary
            mode: Operating mode (default: autonomous)
        """
        self.name = name
        self.mode = mode
        self.llm = AgentLLM(name=f"{name}_llm", config=config)
        self.reasoning = self._create_reasoning(config.get("reasoning", {}))
        self.resources: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"dxa.agent.{name}")
        self._is_running = False

    def _create_reasoning(self, config: Dict[str, Any]) -> BaseReasoning:
        """Create reasoning system based on config.
        
        Args:
            config: Reasoning configuration dictionary
            
        Returns:
            Initialized reasoning system
            
        Raises:
            ValueError: If strategy is unknown
        """
        strategy = config.get("strategy", "cot")
        
        # Get reasoning class
        reasoning_class = self.REASONING_STRATEGIES.get(strategy)
        if not reasoning_class:
            raise ValueError(
                f"Unknown reasoning strategy: {strategy}. "
                f"Valid strategies are: {list(self.REASONING_STRATEGIES.keys())}"
            )
        
        # Create reasoning config
        reasoning_config = ReasoningConfig(**config)
        
        # Initialize reasoning system
        reasoning = reasoning_class()
        reasoning.config = reasoning_config
        return reasoning

    @abstractmethod
    async def run(self) -> Dict[str, Any]:
        """Run the agent.
        
        Returns:
            Dict containing results of the agent's execution
        """
        raise NotImplementedError

    async def initialize(self) -> None:
        """Initialize agent and resources."""
        await self.llm.initialize()
        await self.reasoning.initialize()

        for resource in self.resources.values():
            if callable(getattr(resource, "initialize", None)):
                await resource.initialize()
            
        self.logger.info(
            "Agent initialized with resources: %s",
            list(self.resources.keys())
        )

    async def cleanup(self) -> None:
        """Clean up agent and resources."""
        for resource in self.resources.values():
            if callable(getattr(resource, "cleanup", None)):
                await resource.cleanup()
        
        await self.reasoning.cleanup()
        await self.llm.cleanup()
        
        self.logger.info("Agent cleaned up")

    async def use_expert(self, domain: str, request: str) -> str:
        """Use expert for specialized domain knowledge.
        
        Finds and queries an expert resource for domain-specific knowledge.
        
        Args:
            domain: Domain of expertise required (e.g., "mathematics", "physics")
            request: Query/request for the expert
            
        Returns:
            Expert's response as string
            
        Raises:
            ValueError: If no expert is found for the specified domain
            
        Example:
            ```python
            response = await agent.use_expert(
                domain="mathematics",
                request="Solve: 2x + 5 = 13"
            )
            ```
        """
        experts = {
            name: resource for name, resource in self.resources.items()
            if isinstance(resource, ExpertResource)
        }
        
        expert = next(
            (e for e in experts.values() if e.expertise.name.lower() == domain.lower()),
            None
        )
        
        if not expert:
            raise ValueError(f"No expert found for domain: {domain}")
            
        response = await expert.query({"prompt": request})
        return response["response"]

    async def handle_error(self, error: Exception) -> None:
        """Handle errors during agent execution."""
        self.logger.error("Agent error: %s", str(error))

    async def run_with_progress(self, task: Dict[str, Any]) -> AsyncIterator[AgentProgress]:
        """Run a task with progress updates.
        
        Args:
            task: Task configuration dictionary
            
        Yields:
            AgentProgress objects containing progress or result information
            
        Raises:
            ReasoningError: If reasoning system fails
            ConfigurationError: If agent is misconfigured
            AgentError: If agent operations fail
            ResourceError: If resource operations fail
            DXAConnectionError: If connections fail
            ValueError: If task parameters are invalid
        """
        try:
            # Initial progress
            yield AgentProgress(
                type="progress",
                message="Starting task",
                percent=0
            )
            
            # Run the task with intermediate updates
            result = await self.run()
            
            # Final progress with result
            yield AgentProgress(
                type="result",
                message="Task completed",
                percent=100,
                result=result
            )
            
        except (
            ReasoningError,
            ConfigurationError,
            AgentError,
            ResourceError,
            DXAConnectionError,
            ValueError
        ) as e:
            # Error progress with specific error information
            yield AgentProgress(
                type="result",
                message=f"Task failed: {str(e)}",
                result={
                    "success": False,
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
