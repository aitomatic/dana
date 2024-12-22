"""
Global DXA Factory
"""

from typing import Dict, Any, Union
from .core.agent.agent import Agent
from .core.agent.agent_factory import AgentFactory
from .core.planning.planner_factory import PlannerFactory
from .core.reasoning.reasoner_factory import ReasonerFactory
from .core.planning.base_planner import BasePlanner
from .core.reasoning.base_reasoner import BaseReasoner

class DXAFactory:
    """Creates and configures DXA components."""
    
    @classmethod
    def create_agent(cls, config: Dict[str, Any]) -> Agent:
        """Create an agent with configuration."""
        return AgentFactory.create_agent(config)

    @classmethod
    def create_planner(cls, planner_type: Union[str, BasePlanner] = None) -> BasePlanner:
        """Create planner by calling the planner factory."""
        return PlannerFactory.create_planner(planner_type)

    @classmethod
    def create_reasoner(cls, reasoner_type: Union[str, BaseReasoner] = None) -> BaseReasoner:
        """Create reasoning system."""
        return ReasonerFactory.create_reasoner(reasoner_type)
    