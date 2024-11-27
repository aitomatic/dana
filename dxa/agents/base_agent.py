"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type
import logging
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningConfig
from dxa.core.resources.expert import ExpertResource
from dxa.agents.agent_llm import AgentLLM
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda import OODAReasoning

class BaseAgent(ABC):
    """Base agent with common functionality"""
    
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
    async def run(self, task: str) -> Dict[str, Any]:
        """Run the agent on a task"""
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
        """Use expert for specialized domain knowledge."""
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
