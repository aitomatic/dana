"""
Common functionality for all Agents (above Workflow and Resource).
"""

from .base_wa import BaseWA
from .protocols import AgentProtocol


class BaseA(BaseWA):
    """Base class for Agents common functionality."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agents: list[AgentProtocol] = kwargs.get("agents") or []

    def with_agents(self, *agents: AgentProtocol) -> "BaseWA":
        """Add sub-agents to the agent."""
        if agents and len(agents) > 0:
            for agent in agents:
                if agent not in self._agents:
                    self._agents.append(agent)
        return self

    def add_agent(self, agent: AgentProtocol) -> None:
        """
        Add a single agent to the object.

        Args:
            agent: AgentProtocol instance to add
        """
        if agent not in self._agents:
            self._agents.append(agent)

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent by its ID.

        Args:
            agent_id: ID of the agent to remove

        Returns:
            True if agent was found and removed, False otherwise
        """
        for i, agent in enumerate(self._agents):
            if agent.object_id == agent_id:
                self._agents.pop(i)
                return True
        return False
