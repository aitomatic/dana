"""Factory for creating DXA agents."""

from typing import Dict, Any
from .agent import Agent

class AgentFactory:
    """Creates and configures DXA agents."""
    
    @classmethod
    def create_agent(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent with the given configuration."""
        # Sync construction only
        agent = Agent(name=config.get("name"))
        if "llm_config" in config:
            agent.with_llm(config["llm_config"])
        # ... other config
        return agent
