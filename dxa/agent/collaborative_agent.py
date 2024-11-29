"""Collaborative agent implementation.

This module provides an agent implementation that can work with other agents
to accomplish tasks. It enables agent-to-agent communication, task delegation,
and result aggregation.
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.resource.agents import AgentResource
from dxa.core.reasoning.cot import ChainOfThoughtReasoning

class CollaborativeAgent(BaseAgent):
    """Agent that collaborates with other agents to accomplish tasks.
    
    This agent type extends BaseAgent with capabilities for consulting
    and collaborating with other agents. It maintains a history of collaborations
    and can coordinate multi-agent tasks.
    
    Attributes:
        agent_resource: Resource for accessing other agents
        collaborations: History of agent collaborations
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        agent_registry: Dictionary mapping agent IDs to agent instances
        reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
        description: Optional agent description
        max_iterations: Optional maximum number of iterations (defaults to None)
    """
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        agent_registry: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """Initialize collaborative agent."""
        config = {
            "llm": llm_config,
            "description": description,
            "logging": llm_config.get("logging", {})
        }
        
        super().__init__(
            name=name,
            config=config,
            max_iterations=max_iterations
        )
        
        self.reasoning = reasoning or ChainOfThoughtReasoning()
        self.agent_resource = AgentResource(
            name=f"{name}_agents",
            agent_registry=agent_registry
        )
        self.collaborations: Dict[str, Any] = {}
        self._is_running = True