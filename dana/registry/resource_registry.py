from __future__ import annotations

"""
Resource Registry for Dana

Specialized registry for resource instance tracking and lifecycle management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import TYPE_CHECKING, Any

from dana.registry.instance_registry import StructRegistry

if TYPE_CHECKING:
    from dana.core.resource.resource_instance import ResourceInstance


class ResourceRegistry(StructRegistry["ResourceInstance"]):
    """Specialized registry for tracking resource instances.

    This registry provides resource-specific tracking capabilities with
    additional metadata and lifecycle management for resource instances.
    """

    def __init__(self):
        """Initialize the resource registry."""
        super().__init__()

        # Resource-specific metadata
        self._resource_types: dict[str, str] = {}  # instance_id -> resource_type
        self._resource_providers: dict[str, str] = {}  # instance_id -> provider
        self._resource_status: dict[str, str] = {}  # instance_id -> status
        self._resource_permissions: dict[str, list[str]] = {}  # instance_id -> permissions

    def track_resource(
        self,
        resource: ResourceInstance,
        name: str | None = None,
        resource_type: str | None = None,
        provider: str | None = None,
        permissions: list[str] | None = None,
    ) -> str:
        """Track a resource instance with resource-specific metadata.

        Args:
            resource: The resource StructInstance to track
            name: Optional custom name for the resource
            resource_type: Optional type of the resource (e.g., "database", "api", "file")
            provider: Optional provider of the resource
            permissions: Optional list of permissions for the resource

        Returns:
            The resource instance ID
        """
        instance_id = self.track_instance(resource, name)

        # Store resource-specific metadata
        if resource_type:
            self._resource_types[instance_id] = resource_type
        if provider:
            self._resource_providers[instance_id] = provider
        if permissions:
            self._resource_permissions[instance_id] = permissions
        self._resource_status[instance_id] = "available"

        return instance_id

    def untrack_resource(self, instance_id: str) -> bool:
        """Remove a resource from tracking.

        Args:
            instance_id: The resource instance ID to untrack

        Returns:
            True if the resource was successfully untracked, False if not found
        """
        if not self.untrack_instance(instance_id):
            return False

        # Clean up resource-specific metadata
        self._resource_types.pop(instance_id, None)
        self._resource_providers.pop(instance_id, None)
        self._resource_status.pop(instance_id, None)
        self._resource_permissions.pop(instance_id, None)

        return True

    def get_resource_type(self, instance_id: str) -> str | None:
        """Get the type of a resource.

        Args:
            instance_id: The resource instance ID

        Returns:
            The resource's type, or None if not set
        """
        return self._resource_types.get(instance_id)

    def get_resource_provider(self, instance_id: str) -> str | None:
        """Get the provider of a resource.

        Args:
            instance_id: The resource instance ID

        Returns:
            The resource's provider, or None if not set
        """
        return self._resource_providers.get(instance_id)

    def get_resource_status(self, instance_id: str) -> str:
        """Get the status of a resource.

        Args:
            instance_id: The resource instance ID

        Returns:
            The resource's status
        """
        return self._resource_status.get(instance_id, "unknown")

    def set_resource_status(self, instance_id: str, status: str) -> bool:
        """Set the status of a resource.

        Args:
            instance_id: The resource instance ID
            status: The new status

        Returns:
            True if the resource exists and status was set, False otherwise
        """
        if instance_id not in self._instances:
            return False
        self._resource_status[instance_id] = status
        return True

    def get_resource_permissions(self, instance_id: str) -> list[str]:
        """Get the permissions of a resource.

        Args:
            instance_id: The resource instance ID

        Returns:
            List of resource permissions, or empty list if not set
        """
        return self._resource_permissions.get(instance_id, [])

    def add_resource_permission(self, instance_id: str, permission: str) -> bool:
        """Add a permission to a resource.

        Args:
            instance_id: The resource instance ID
            permission: The permission to add

        Returns:
            True if the resource exists and permission was added, False otherwise
        """
        if instance_id not in self._instances:
            return False
        if instance_id not in self._resource_permissions:
            self._resource_permissions[instance_id] = []
        if permission not in self._resource_permissions[instance_id]:
            self._resource_permissions[instance_id].append(permission)
        return True

    def remove_resource_permission(self, instance_id: str, permission: str) -> bool:
        """Remove a permission from a resource.

        Args:
            instance_id: The resource instance ID
            permission: The permission to remove

        Returns:
            True if the resource exists and permission was removed, False otherwise
        """
        if instance_id not in self._instances:
            return False
        if instance_id in self._resource_permissions:
            self._resource_permissions[instance_id] = [p for p in self._resource_permissions[instance_id] if p != permission]
        return True

    def get_resources_by_type(self, resource_type: str) -> dict[str, ResourceInstance]:
        """Get all resources of a specific type.

        Args:
            resource_type: The resource type to filter by

        Returns:
            Dictionary of resource instances with the specified type
        """
        return {
            instance_id: resource
            for instance_id, resource in self._instances.items()
            if self._resource_types.get(instance_id) == resource_type
        }

    def get_resources_by_provider(self, provider: str) -> dict[str, ResourceInstance]:
        """Get all resources from a specific provider.

        Args:
            provider: The provider to filter by

        Returns:
            Dictionary of resource instances from the specified provider
        """
        return {
            instance_id: resource
            for instance_id, resource in self._instances.items()
            if self._resource_providers.get(instance_id) == provider
        }

    def get_available_resources(self) -> dict[str, ResourceInstance]:
        """Get all available resources.

        Returns:
            Dictionary of available resource instances
        """
        return {
            instance_id: resource
            for instance_id, resource in self._instances.items()
            if self._resource_status.get(instance_id) == "available"
        }

    def get_resource_metadata_for_llm(self, instance_id: str) -> dict[str, Any] | None:
        """Get LLM-friendly metadata from ResourceInstance.

        Args:
            instance_id: The resource instance ID

        Returns:
            Dictionary of metadata suitable for LLM decision-making, or None if not found
        """
        resource = self._instances.get(instance_id)
        if not resource:
            return None

        # Extract metadata from the ResourceInstance's built-in fields
        metadata = {
            "instance_id": instance_id,
            "name": getattr(resource, "name", ""),
            "kind": getattr(resource, "kind", ""),
            "resource_type": self._resource_types.get(instance_id, ""),
            "provider": self._resource_providers.get(instance_id, ""),
            "status": self._resource_status.get(instance_id, "unknown"),
            "permissions": self._resource_permissions.get(instance_id, []),
        }

        # Add built-in metadata from ResourceInstance
        if hasattr(resource, "get_metadata"):
            metadata["builtin_metadata"] = resource.get_metadata()
        if hasattr(resource, "resource_type"):
            metadata["docstring"] = resource.resource_type.docstring
            metadata["field_comments"] = resource.resource_type.field_comments
            metadata["fields"] = resource.resource_type.fields

        return metadata

    def match_resource_for_llm(self, query: str, context: dict[str, Any]) -> tuple[float, ResourceInstance | None, dict[str, Any] | None]:
        """Match resource for LLM decision-making.

        Args:
            query: The search query
            context: Context entities for matching

        Returns:
            Tuple of (confidence_score, ResourceInstance or None, metadata or None)
        """
        query_lower = query.lower()
        best_score = 0.0
        best_resource = None
        best_metadata = None

        for instance_id, resource in self._instances.items():
            metadata = self.get_resource_metadata_for_llm(instance_id)
            if not metadata:
                continue

            # Calculate match score based on name, kind, type, and metadata
            score = 0.0

            # Match by name
            if metadata.get("name", "").lower() in query_lower:
                score += 0.8

            # Match by kind
            if metadata.get("kind", "").lower() in query_lower:
                score += 0.7

            # Match by resource type
            if metadata.get("resource_type", "").lower() in query_lower:
                score += 0.6

            # Match by provider
            if metadata.get("provider", "").lower() in query_lower:
                score += 0.5

            # Match by docstring
            docstring = metadata.get("docstring", "")
            if docstring and any(word in docstring.lower() for word in query_lower.split()):
                score += 0.4

            # Match by field comments
            field_comments = metadata.get("field_comments", {})
            for comment in field_comments.values():
                if any(word in comment.lower() for word in query_lower.split()):
                    score += 0.2

            if score > best_score:
                best_score = score
                best_resource = resource
                best_metadata = metadata

        return best_score, best_resource, best_metadata

    def pack_resources_for_llm(self, entities: dict[str, Any]) -> dict[str, ResourceInstance]:
        """Pack resources for LLM context based on entities.

        Args:
            entities: Context entities for resource selection

        Returns:
            Dictionary of packed ResourceInstance objects
        """
        packed = {}

        # Simple selection logic - can be enhanced with more sophisticated selection
        for instance_id, resource in self._instances.items():
            if self._should_include_resource_for_llm(instance_id, resource, entities):
                packed[instance_id] = resource

        return packed

    def _should_include_resource_for_llm(self, instance_id: str, resource: ResourceInstance, entities: dict[str, Any]) -> bool:
        """Determine if a resource should be included for LLM context based on entities."""
        # Simple implementation - can be enhanced with more sophisticated selection
        # For now, include all available resources
        return self._resource_status.get(instance_id) == "available"

    def clear(self) -> None:
        """Clear all resources and their metadata."""
        super().clear()
        self._resource_types.clear()
        self._resource_providers.clear()
        self._resource_status.clear()
        self._resource_permissions.clear()
