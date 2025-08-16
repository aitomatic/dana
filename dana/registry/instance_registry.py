"""
Instance Registry for Dana

Optional registry for instance tracking and lifecycle management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any


class InstanceRegistry:
    """Optional registry for tracking instances globally.

    This registry provides instance tracking capabilities for debugging,
    monitoring, and lifecycle management. It's optional and doesn't affect
    the core functionality of Dana's type system.
    """

    def __init__(self):
        """Initialize the instance registry with instance-specific storage."""
        # Instance storage by category
        self._agent_instances: dict[str, Any] = {}
        self._resource_instances: dict[str, Any] = {}

        # Instance metadata and lifecycle tracking
        self._instance_metadata: dict[str, dict[str, Any]] = {}
        self._instance_creation_times: dict[str, float] = {}
        self._instance_states: dict[str, str] = {}  # "active", "inactive", "destroyed"

        # Instance relationships
        self._instance_owners: dict[str, str] = {}  # instance_id -> owner_agent
        self._agent_owned_instances: dict[str, set[str]] = {}  # agent -> set of instance_ids

        # Instance counters
        self._instance_counters: dict[str, int] = {
            "agent": 0,
            "resource": 0,
        }

    # === Agent Instance Methods ===

    def track_agent_instance(self, instance: Any, name: str | None = None) -> str:
        """Track an agent instance globally.

        Args:
            instance: The agent instance to track
            name: Optional custom name for the instance

        Returns:
            The instance ID
        """
        instance_id = name or f"agent_{self._instance_counters['agent']}"
        self._instance_counters["agent"] += 1

        self._agent_instances[instance_id] = instance
        self._instance_metadata[instance_id] = {
            "category": "agent",
            "tracked_at": self._get_timestamp(),
            "type_name": self._get_instance_type_name(instance),
        }
        self._instance_creation_times[instance_id] = self._get_timestamp()
        self._instance_states[instance_id] = "active"

        return instance_id

    def get_agent_instance(self, instance_id: str) -> Any | None:
        """Get an agent instance by ID.

        Args:
            instance_id: The instance ID

        Returns:
            The agent instance or None if not found
        """
        return self._agent_instances.get(instance_id)

    def list_agent_instances(self, agent_type: str | None = None) -> list[Any]:
        """List all tracked agent instances.

        Args:
            agent_type: Optional filter by agent type name

        Returns:
            List of agent instances
        """
        instances = list(self._agent_instances.values())
        if agent_type:
            instances = [inst for inst in instances if self._get_instance_type_name(inst) == agent_type]
        return instances

    def list_agent_instance_ids(self, agent_type: str | None = None) -> list[str]:
        """List all tracked agent instance IDs.

        Args:
            agent_type: Optional filter by agent type name

        Returns:
            List of agent instance IDs
        """
        ids = list(self._agent_instances.keys())
        if agent_type:
            ids = [inst_id for inst_id in ids if self._instance_metadata.get(inst_id, {}).get("type_name") == agent_type]
        return ids

    # === Resource Instance Methods ===

    def track_resource_instance(self, instance: Any, name: str | None = None) -> str:
        """Track a resource instance globally.

        Args:
            instance: The resource instance to track
            name: Optional custom name for the instance

        Returns:
            The instance ID
        """
        instance_id = name or f"resource_{self._instance_counters['resource']}"
        self._instance_counters["resource"] += 1

        self._resource_instances[instance_id] = instance
        self._instance_metadata[instance_id] = {
            "category": "resource",
            "tracked_at": self._get_timestamp(),
            "type_name": self._get_instance_type_name(instance),
        }
        self._instance_creation_times[instance_id] = self._get_timestamp()
        self._instance_states[instance_id] = "active"

        return instance_id

    def get_resource_instance(self, instance_id: str) -> Any | None:
        """Get a resource instance by ID.

        Args:
            instance_id: The instance ID

        Returns:
            The resource instance or None if not found
        """
        return self._resource_instances.get(instance_id)

    def list_resource_instances(self, resource_type: str | None = None) -> list[Any]:
        """List all tracked resource instances.

        Args:
            resource_type: Optional filter by resource type name

        Returns:
            List of resource instances
        """
        instances = list(self._resource_instances.values())
        if resource_type:
            instances = [inst for inst in instances if self._get_instance_type_name(inst) == resource_type]
        return instances

    def list_resource_instance_ids(self, resource_type: str | None = None) -> list[str]:
        """List all tracked resource instance IDs.

        Args:
            resource_type: Optional filter by resource type name

        Returns:
            List of resource instance IDs
        """
        ids = list(self._resource_instances.keys())
        if resource_type:
            ids = [inst_id for inst_id in ids if self._instance_metadata.get(inst_id, {}).get("type_name") == resource_type]
        return ids

    # === Generic Instance Methods ===

    def get_instance(self, instance_id: str) -> Any | None:
        """Get any instance by ID (searches all categories).

        Args:
            instance_id: The instance ID

        Returns:
            The instance or None if not found
        """
        # Search in order: agent, resource
        if instance_id in self._agent_instances:
            return self._agent_instances[instance_id]
        elif instance_id in self._resource_instances:
            return self._resource_instances[instance_id]
        return None

    def has_instance(self, instance_id: str) -> bool:
        """Check if an instance is tracked.

        Args:
            instance_id: The instance ID

        Returns:
            True if the instance is tracked
        """
        return instance_id in self._agent_instances or instance_id in self._resource_instances

    def list_all_instances(self) -> list[Any]:
        """List all tracked instances across all categories.

        Returns:
            List of all instances
        """
        instances = []
        instances.extend(self._agent_instances.values())
        instances.extend(self._resource_instances.values())
        return instances

    def list_all_instance_ids(self) -> list[str]:
        """List all tracked instance IDs across all categories.

        Returns:
            List of all instance IDs
        """
        ids = []
        ids.extend(self._agent_instances.keys())
        ids.extend(self._resource_instances.keys())
        return ids

    # === Instance Lifecycle Methods ===

    def set_instance_state(self, instance_id: str, state: str) -> None:
        """Set the state of an instance.

        Args:
            instance_id: The instance ID
            state: The new state ("active", "inactive", "destroyed")
        """
        if instance_id in self._instance_states:
            self._instance_states[instance_id] = state

    def get_instance_state(self, instance_id: str) -> str | None:
        """Get the state of an instance.

        Args:
            instance_id: The instance ID

        Returns:
            The instance state or None if not found
        """
        return self._instance_states.get(instance_id)

    def get_instance_metadata(self, instance_id: str) -> dict[str, Any] | None:
        """Get metadata for an instance.

        Args:
            instance_id: The instance ID

        Returns:
            Instance metadata or None if not found
        """
        return self._instance_metadata.get(instance_id)

    def get_instance_creation_time(self, instance_id: str) -> float | None:
        """Get the creation time of an instance.

        Args:
            instance_id: The instance ID

        Returns:
            Creation timestamp or None if not found
        """
        return self._instance_creation_times.get(instance_id)

    def set_instance_owner(self, instance_id: str, owner_agent: str) -> None:
        """Set the owner agent for an instance.

        Args:
            instance_id: The instance ID
            owner_agent: The agent that owns this instance
        """
        self._instance_owners[instance_id] = owner_agent

        # Update agent-instance relationship
        if owner_agent not in self._agent_owned_instances:
            self._agent_owned_instances[owner_agent] = set()
        self._agent_owned_instances[owner_agent].add(instance_id)

    def get_instance_owner(self, instance_id: str) -> str | None:
        """Get the owner agent for an instance.

        Args:
            instance_id: The instance ID

        Returns:
            The owner agent name or None if not found
        """
        return self._instance_owners.get(instance_id)

    def get_agent_owned_instances(self, agent_name: str) -> set[str]:
        """Get all instances owned by an agent.

        Args:
            agent_name: The agent name

        Returns:
            Set of instance IDs owned by the agent
        """
        return self._agent_owned_instances.get(agent_name, set()).copy()

    # === Utility Methods ===

    def clear(self) -> None:
        """Clear all tracked instances (for testing)."""
        self._agent_instances.clear()
        self._resource_instances.clear()
        self._instance_metadata.clear()
        self._instance_creation_times.clear()
        self._instance_states.clear()
        self._instance_owners.clear()
        self._agent_owned_instances.clear()
        self._instance_counters = {"agent": 0, "resource": 0}

    def count(self) -> int:
        """Get the total number of tracked instances."""
        return len(self._agent_instances) + len(self._resource_instances)

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return self.count() == 0

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about tracked instances."""
        return {
            "total_instances": self.count(),
            "agent_instances": len(self._agent_instances),
            "resource_instances": len(self._resource_instances),
            "active_instances": sum(1 for state in self._instance_states.values() if state == "active"),
            "inactive_instances": sum(1 for state in self._instance_states.values() if state == "inactive"),
            "destroyed_instances": sum(1 for state in self._instance_states.values() if state == "destroyed"),
        }

    def _get_instance_type_name(self, instance: Any) -> str | None:
        """Get the type name from an instance.

        Args:
            instance: The instance to extract type from

        Returns:
            The type name or None if unable to determine
        """
        # Try to get from struct_type attribute
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            if hasattr(struct_type, "name"):
                return struct_type.name

        # Try to get from agent_type attribute
        if hasattr(instance, "agent_type"):
            agent_type = instance.agent_type
            if hasattr(agent_type, "name"):
                return agent_type.name

        # Try to get from resource_type attribute
        if hasattr(instance, "resource_type"):
            resource_type = instance.resource_type
            if hasattr(resource_type, "name"):
                return resource_type.name

        # Try to get from class name
        if hasattr(instance, "__class__"):
            return instance.__class__.__name__

        return None

    def _get_timestamp(self) -> float:
        """Get current timestamp for tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the instance registry."""
        stats = self.get_statistics()
        return (
            f"InstanceRegistry("
            f"total={stats['total_instances']}, "
            f"agents={stats['agent_instances']}, "
            f"resources={stats['resource_instances']}, "
            f"active={stats['active_instances']}"
            f")"
        )
