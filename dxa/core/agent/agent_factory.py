"""Factory for creating DXA agents."""

from typing import Dict, Any
from .agent import Agent
from ..planning.planner_factory import PlannerFactory
from ..reasoning.reasoner_factory import ReasonerFactory
from ..resource.llm_resource import LLMResource

class AgentFactory:
    """Creates and configures DXA agents."""
    
    @classmethod
    async def create_agent(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent with the given configuration."""
        # Create core components
        planner = PlannerFactory.create_planner(config.get("planner"))
        reasoner = ReasonerFactory.create_reasoner(config.get("reasoner"))
        
        # Create agent_llm
        llm_config = config.get("llm_config", {})
        agent_llm = LLMResource(
            name=f"{config.get('name', 'agent')}_llm",
            config=llm_config
        )
        
        # Create other resources
        resources = config.get("resources", {})
        
        return Agent(name=config.get("name")) \
            .with_planner(planner) \
            .with_reasoner(reasoner) \
            .with_llm(agent_llm) \
            .with_resources(resources)
