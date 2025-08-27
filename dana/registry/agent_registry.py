from __future__ import annotations

"""
Agent Registry for Dana

Specialized registry for agent instance tracking and lifecycle management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import TYPE_CHECKING

from dana.registry.instance_registry import StructRegistry

if TYPE_CHECKING:
    from dana.core.builtin_types.agent_system import AgentInstance


class AgentRegistry(StructRegistry["AgentInstance"]):
    """Specialized registry for tracking agent instances.

    This registry provides agent-specific tracking capabilities with
    additional metadata and lifecycle management for agent instances.
    """

    def __init__(self):
        """Initialize the agent registry."""
        super().__init__()

        # Agent-specific metadata
        self._agent_roles: dict[str, str] = {}  # instance_id -> role
        self._agent_capabilities: dict[str, list[str]] = {}  # instance_id -> capabilities
        self._agent_status: dict[str, str] = {}  # instance_id -> status

    def track_agent(
        self, agent: AgentInstance, name: str | None = None, role: str | None = None, capabilities: list[str] | None = None
    ) -> str:
        """Track an agent instance with agent-specific metadata.

        Args:
            agent: The agent StructInstance to track
            name: Optional custom name for the agent
            role: Optional role for the agent (e.g., "researcher", "coder", "planner")
            capabilities: Optional list of agent capabilities

        Returns:
            The agent instance ID
        """
        instance_id = self.track_instance(agent, name)

        # Store agent-specific metadata
        if role:
            self._agent_roles[instance_id] = role
        if capabilities:
            self._agent_capabilities[instance_id] = capabilities
        self._agent_status[instance_id] = "active"

        return instance_id

    def untrack_agent(self, instance_id: str) -> bool:
        """Remove an agent from tracking.

        Args:
            instance_id: The agent instance ID to untrack

        Returns:
            True if the agent was successfully untracked, False if not found
        """
        if not self.untrack_instance(instance_id):
            return False

        # Clean up agent-specific metadata
        self._agent_roles.pop(instance_id, None)
        self._agent_capabilities.pop(instance_id, None)
        self._agent_status.pop(instance_id, None)

        return True

    def get_agent_role(self, instance_id: str) -> str | None:
        """Get the role of an agent.

        Args:
            instance_id: The agent instance ID

        Returns:
            The agent's role, or None if not set
        """
        return self._agent_roles.get(instance_id)

    def get_agent_capabilities(self, instance_id: str) -> list[str]:
        """Get the capabilities of an agent.

        Args:
            instance_id: The agent instance ID

        Returns:
            List of agent capabilities, or empty list if not set
        """
        return self._agent_capabilities.get(instance_id, [])

    def get_agent_status(self, instance_id: str) -> str:
        """Get the status of an agent.

        Args:
            instance_id: The agent instance ID

        Returns:
            The agent's status
        """
        return self._agent_status.get(instance_id, "unknown")

    def set_agent_status(self, instance_id: str, status: str) -> bool:
        """Set the status of an agent.

        Args:
            instance_id: The agent instance ID
            status: The new status

        Returns:
            True if the agent exists and status was set, False otherwise
        """
        if instance_id not in self._instances:
            return False
        self._agent_status[instance_id] = status
        return True

    def get_agents_by_role(self, role: str) -> dict[str, AgentInstance]:
        """Get all agents with a specific role.

        Args:
            role: The role to filter by

        Returns:
            Dictionary of agent instances with the specified role
        """
        return {instance_id: agent for instance_id, agent in self._instances.items() if self._agent_roles.get(instance_id) == role}

    def get_active_agents(self) -> dict[str, AgentInstance]:
        """Get all active agents.

        Returns:
            Dictionary of active agent instances
        """
        return {instance_id: agent for instance_id, agent in self._instances.items() if self._agent_status.get(instance_id) == "active"}

    def clear(self) -> None:
        """Clear all agents and their metadata."""
        super().clear()
        self._agent_roles.clear()
        self._agent_capabilities.clear()
        self._agent_status.clear()
