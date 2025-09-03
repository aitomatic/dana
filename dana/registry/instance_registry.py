"""
Instance Registry for Dana

Optional registry for instance tracking and lifecycle management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Generic, TypeVar

from dana.common.mixins.registry_observable import RegistryObservable
from dana.core.builtin_types.struct_system import StructInstance

InstanceT = TypeVar("InstanceT", bound=StructInstance)


class StructRegistry(RegistryObservable[InstanceT], Generic[InstanceT]):
    """Optional registry for tracking StructInstance objects globally.

    This registry provides instance tracking capabilities for debugging,
    monitoring, and lifecycle management. It's optional and doesn't affect
    the core functionality of Dana's type system.
    """

    def __init__(self):
        """Initialize the instance registry with unified storage."""
        super().__init__()

        # Unified instance storage
        self._instances: dict[str, InstanceT] = {}

        # Instance metadata and lifecycle tracking
        self._instance_metadata: dict[str, dict[str, Any]] = {}
        self._instance_creation_times: dict[str, float] = {}
        self._instance_states: dict[str, str] = {}  # "active", "inactive", "destroyed"

        # Instance relationships
        self._instance_owners: dict[str, str] = {}  # instance_id -> owner_agent
        self._agent_owned_instances: dict[str, set[str]] = {}  # agent -> set of instance_ids

        # Instance counter
        self._instance_counter: int = 0

    def track_instance(self, instance: InstanceT, name: str | None = None) -> str:
        """Track a StructInstance globally.

        Args:
            instance: The StructInstance to track
            name: Optional custom name for the instance

        Returns:
            The instance ID
        """
        if not isinstance(instance, StructInstance):
            raise TypeError(f"StructRegistry can only track StructInstance objects, got {type(instance)}")

        instance_id = instance.instance_id
        self._instance_counter += 1

        self._instances[instance_id] = instance
        self._instance_metadata[instance_id] = {
            "name": name,
            "tracked_at": self._get_timestamp(),
            "type_name": self._get_instance_type_name(instance),
            "instance_type": type(instance).__name__,
        }
        self._instance_creation_times[instance_id] = self._get_timestamp()
        self._instance_states[instance_id] = "active"

        # Trigger registration event
        self._trigger_event("registered", instance_id, instance)

        return instance_id

    def untrack_instance(self, instance_id: str) -> bool:
        """Remove a StructInstance from tracking and release all associated resources.

        Args:
            instance_id: The instance ID to untrack

        Returns:
            True if the instance was successfully untracked, False if not found
        """
        if instance_id not in self._instances:
            return False

        # Get the instance before removing it for event triggering
        instance = self._instances[instance_id]

        # Remove the instance from storage
        del self._instances[instance_id]

        # Clean up all associated metadata and tracking data
        self._instance_metadata.pop(instance_id, None)
        self._instance_creation_times.pop(instance_id, None)
        self._instance_states.pop(instance_id, None)

        # Clean up ownership relationships
        owner = self._instance_owners.pop(instance_id, None)
        if owner and owner in self._agent_owned_instances:
            self._agent_owned_instances[owner].discard(instance_id)
            # Clean up empty agent entries
            if not self._agent_owned_instances[owner]:
                del self._agent_owned_instances[owner]

        # Trigger unregistration event
        self._trigger_event("unregistered", instance_id, instance)

        return True

    def get_instance(self, instance_id: str) -> InstanceT | None:
        """Get a StructInstance by ID.

        Args:
            instance_id: The instance ID

        Returns:
            The StructInstance or None if not found
        """
        return self._instances.get(instance_id)

    def list_instances(self, instance_type: str | None = None) -> list[InstanceT]:
        """List all tracked StructInstance objects.

        Args:
            instance_type: Optional filter by instance type name (e.g., "AgentInstance", "ResourceInstance")

        Returns:
            List of StructInstance objects
        """
        instances = list(self._instances.values())
        if instance_type:
            instances = [inst for inst in instances if type(inst).__name__ == instance_type]
        return instances

    def list_instance_ids(self, instance_type: str | None = None) -> list[str]:
        """List all tracked instance IDs.

        Args:
            instance_type: Optional filter by instance type name

        Returns:
            List of instance IDs
        """
        ids = list(self._instances.keys())
        if instance_type:
            ids = [inst_id for inst_id in ids if self._instance_metadata.get(inst_id, {}).get("instance_type") == instance_type]
        return ids

    def has_instance(self, instance_id: str) -> bool:
        """Check if an instance is tracked.

        Args:
            instance_id: The instance ID

        Returns:
            True if the instance is tracked
        """
        return instance_id in self._instances

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
        # Trigger unregistration events for all instances before clearing
        for instance_id, instance in list(self._instances.items()):
            self._trigger_event("unregistered", instance_id, instance)

        self._instances.clear()
        self._instance_metadata.clear()
        self._instance_creation_times.clear()
        self._instance_states.clear()
        self._instance_owners.clear()
        self._agent_owned_instances.clear()
        self._instance_counter = 0

    def count(self) -> int:
        """Get the total number of tracked instances."""
        return len(self._instances)

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return self.count() == 0

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about tracked instances."""
        instance_types = {}
        for metadata in self._instance_metadata.values():
            instance_type = metadata.get("instance_type", "Unknown")
            instance_types[instance_type] = instance_types.get(instance_type, 0) + 1

        return {
            "total_instances": self.count(),
            "instance_types": instance_types,
            "active_instances": sum(1 for state in self._instance_states.values() if state == "active"),
            "inactive_instances": sum(1 for state in self._instance_states.values() if state == "inactive"),
            "destroyed_instances": sum(1 for state in self._instance_states.values() if state == "destroyed"),
        }

    def _get_instance_type_name(self, instance: StructInstance) -> str | None:
        """Get the type name from a StructInstance.

        Args:
            instance: The StructInstance to extract type from

        Returns:
            The type name or None if unable to determine
        """
        # Try to get from struct_type attribute
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            if hasattr(struct_type, "name"):
                return struct_type.name

        # Try to get from class name
        if hasattr(instance, "__class__"):
            return instance.__class__.__name__

        return None

    def _get_timestamp(self) -> float:
        """Get current timestamp for tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the struct registry."""
        stats = self.get_statistics()
        return f"StructRegistry(total={stats['total_instances']}, types={stats['instance_types']}, active={stats['active_instances']})"
