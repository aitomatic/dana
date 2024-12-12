"""Base implementation for DXA agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class providing common agent functionality."""
    
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
        self.config = config

    async def initialize(self) -> None:
        """Initialize agent."""
        pass

    async def cleanup(self) -> None:
        """Clean up agent."""
        pass

    async def run(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent.
        
        Args:
            query: Query parameters
            
        Returns:
            Response dictionary
        """
        pass

    @abstractmethod
    def get_agent_system_prompt(self) -> str:
        """Get the agent-specific system prompt."""
        pass

    @abstractmethod
    def get_agent_user_prompt(self) -> str:
        """Get the agent-specific user prompt."""
        pass
