"""
AgentPool - Manages a collection of A2A agents and provides selection functionality.

This module provides the AgentPool class for managing multiple A2A agents and selecting
the most appropriate agent for a given task based on skills.
"""

# TODO: Update to use new agent struct system
# from dana.core.builtin_types.agent_system.abstract_dana_agent import AbstractDanaAgent
from typing import Any

from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.core.lang.sandbox_context import SandboxContext

from .agent_selector import AgentSelector


class AgentPool(BaseSysResource):
    """Manages a pool of A2A agents and provides selection/querying."""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        agents: list | None = None,  # TODO: Type as AgentStructInstance
        exclude_self: bool = False,
        context: SandboxContext | None = None,
    ):
        """Initialize agent pool.

        Args:
            name: Pool identifier
            agent_configs: Optional list of agent configurations to initialize agents
            agents: Optional dictionary of pre-initialized agents
            description: Optional pool description

        Raises:
            ValueError: If neither agent_configs nor agents is provided
        """
        super().__init__(name, description)
        self.agents: dict[str, Any] = {}  # TODO: Type as AgentStructInstance
        self._selector = None
        self.context = context
        self.exclude_self = exclude_self
        # Initialize from pre-existing agents if provided
        if agents:
            for agent in agents:
                self.agents[agent.name] = agent

        # Ensure at least one agent is provided
        if not self.agents:
            raise ValueError("Must provide at least one agent")

    @property
    def selector(self) -> AgentSelector:
        """Get or create agent selector."""
        if self._selector is None:
            self._selector = AgentSelector(self)
        return self._selector

    def list_agents(self) -> list[str]:
        """List all agents in the pool.

        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def get_agent(self, name: str) -> Any:  # TODO: Return AgentStructInstance
        """Get an agent by name.

        Args:
            name: Agent name

        Returns:
            A2AResource instance

        Raises:
            KeyError: If agent not found
        """
        if name not in self.agents:
            raise KeyError(f"Agent not found: {name}")
        return self.agents[name]

    def select_agent(
        self, task: any, strategy: str = "llm", included_resources: list[str | BaseSysResource] | None = None
    ) -> Any | None:  # TODO: Return AgentStructInstance | None
        """Select an agent based on task requirements.

        Args:
            task: Task requirements including description and skills
            strategy: Selection strategy ("skill" or "llm")
            included_resources: Optional list of resource names or resources to include when generating self agent card

        Returns:
            Selected A2AResource instance or None if no suitable agent

        Raises:
            ValueError: If no suitable agent found
        """
        return self.selector.select_agent(task, strategy, included_resources=included_resources)

    def get_agent_cards(self, included_resources: list[str | BaseSysResource] | None = None) -> dict[str, dict]:
        """Get agent cards for all agents in the pool.

        Args:
            included_resources: Optional list of resource names or resources to include when generating self agent card

        Returns:
            Dictionary mapping agent names to their cards (with skills)
        """
        agent_cards = {
            name: {**agent.agent_card, "skills": agent.agent_card.get("skills", agent.agent_card.get("capabilities", []))}
            for name, agent in self.agents.items()
        }
        if self.context and not self.exclude_self:
            agent_cards.update(self.context.get_self_agent_card(included_resources=included_resources))
        return agent_cards

    def refresh_agent_cards(self) -> None:
        """Force refresh agent cards for all agents."""
        for agent in self.agents.values():
            agent.refresh_agent_card()

    def add_agent(self, agent: Any) -> None:  # TODO: Accept AgentStructInstance
        """Add an agent to the pool.

        Args:
            agent: A2AResource instance to add

        Raises:
            ValueError: If agent with same name already exists
        """
        if agent.name in self.agents:
            raise ValueError(f"Agent with name '{agent.name}' already exists in pool")
        self.agents[agent.name] = agent

    def remove_agent(self, name: str) -> None:
        """Remove an agent from the pool.

        Args:
            name: Name of agent to remove

        Raises:
            KeyError: If agent not found
        """
        if name not in self.agents:
            raise KeyError(f"Agent not found: {name}")
        del self.agents[name]
