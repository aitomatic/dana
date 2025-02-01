"""
Global DXA Factory
"""

from typing import Dict, Any
from ..agent import Agent, AgentFactory

class DXAFactory:
    """Creates and configures DXA components."""
    
    @classmethod
    def create_agent(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent with configuration."""
        return AgentFactory.create_agent(config)
