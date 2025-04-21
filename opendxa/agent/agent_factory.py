"""Factory for creating DXA agents."""

from typing import Dict, Any
from opendxa.agent.agent import Agent
from opendxa.config.agent_config import AgentConfig

class AgentFactory:
    """Creates and configures DXA agents."""
    
    @classmethod
    def create_agent(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent with the given configuration."""
        # Create agent with name
        agent = Agent(name=config.get("name"))
        
        # Initialize with config
        agent_config = AgentConfig(config_path=config.get("config_path"), **config)
        agent._config = agent_config
        
        # Configure LLM if specified
        if "llm_config" in config:
            agent.with_llm(config["llm_config"])
            
        return agent
