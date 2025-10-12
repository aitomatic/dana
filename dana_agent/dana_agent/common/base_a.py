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
