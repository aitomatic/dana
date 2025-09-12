from __future__ import annotations

"""
Workflow Registry for Dana

Specialized registry for workflow instance tracking and lifecycle management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import TYPE_CHECKING, Any

from dana.registry.instance_registry import StructRegistry

if TYPE_CHECKING:
    from dana.core.workflow.workflow_system import WorkflowInstance


class WorkflowRegistry(StructRegistry["WorkflowInstance"]):
    """Specialized registry for tracking workflow instances.

    This registry provides workflow-specific tracking capabilities with
    additional metadata and lifecycle management for workflow instances.
    """

    def __init__(self):
        """Initialize the workflow registry."""
        super().__init__()

        # Workflow-specific metadata
        self._workflow_types: dict[str, str] = {}  # instance_id -> workflow_type
        self._workflow_status: dict[str, str] = {}  # instance_id -> status
        self._workflow_execution_history: dict[str, list[dict[str, Any]]] = {}  # instance_id -> execution history
        self._workflow_dependencies: dict[str, list[str]] = {}  # instance_id -> dependencies

    def track_workflow(
        self,
        workflow: WorkflowInstance,
        name: str | None = None,
        workflow_type: str | None = None,
        dependencies: list[str] | None = None,
    ) -> str:
        """Track a workflow instance with workflow-specific metadata.

        Args:
            workflow: The workflow StructInstance to track
            name: Optional custom name for the workflow
            workflow_type: Optional type of the workflow (e.g., "diagnostic", "planning", "execution")
            dependencies: Optional list of dependencies for the workflow

        Returns:
            The workflow instance ID
        """
        instance_id = self.track_instance(workflow, name)

        # Store workflow-specific metadata
        if workflow_type:
            self._workflow_types[instance_id] = workflow_type
        if dependencies:
            self._workflow_dependencies[instance_id] = dependencies
        self._workflow_status[instance_id] = "created"

        return instance_id

    def untrack_workflow(self, instance_id: str) -> bool:
        """Remove a workflow from tracking.

        Args:
            instance_id: The workflow instance ID to untrack

        Returns:
            True if the workflow was successfully untracked, False if not found
        """
        if not self.untrack_instance(instance_id):
            return False

        # Clean up workflow-specific metadata
        self._workflow_types.pop(instance_id, None)
        self._workflow_status.pop(instance_id, None)
        self._workflow_execution_history.pop(instance_id, None)
        self._workflow_dependencies.pop(instance_id, None)

        return True

    def get_workflow_type(self, instance_id: str) -> str | None:
        """Get the type of a workflow.

        Args:
            instance_id: The workflow instance ID

        Returns:
            The workflow's type, or None if not set
        """
        return self._workflow_types.get(instance_id)

    def get_workflow_status(self, instance_id: str) -> str:
        """Get the status of a workflow.

        Args:
            instance_id: The workflow instance ID

        Returns:
            The workflow's status
        """
        return self._workflow_status.get(instance_id, "unknown")

    def set_workflow_status(self, instance_id: str, status: str) -> bool:
        """Set the status of a workflow.

        Args:
            instance_id: The workflow instance ID
            status: The new status

        Returns:
            True if the workflow exists and status was set, False otherwise
        """
        if instance_id not in self._instances:
            return False
        self._workflow_status[instance_id] = status
        return True

    def get_workflow_dependencies(self, instance_id: str) -> list[str]:
        """Get the dependencies of a workflow.

        Args:
            instance_id: The workflow instance ID

        Returns:
            List of workflow dependencies, or empty list if not set
        """
        return self._workflow_dependencies.get(instance_id, [])

    def add_workflow_dependency(self, instance_id: str, dependency: str) -> bool:
        """Add a dependency to a workflow.

        Args:
            instance_id: The workflow instance ID
            dependency: The dependency to add

        Returns:
            True if the workflow exists and dependency was added, False otherwise
        """
        if instance_id not in self._instances:
            return False
        if instance_id not in self._workflow_dependencies:
            self._workflow_dependencies[instance_id] = []
        if dependency not in self._workflow_dependencies[instance_id]:
            self._workflow_dependencies[instance_id].append(dependency)
        return True

    def get_workflows_by_type(self, workflow_type: str) -> dict[str, WorkflowInstance]:
        """Get all workflows of a specific type.

        Args:
            workflow_type: The workflow type to filter by

        Returns:
            Dictionary of workflow instances with the specified type
        """
        return {
            instance_id: workflow
            for instance_id, workflow in self._instances.items()
            if self._workflow_types.get(instance_id) == workflow_type
        }

    def get_workflows_by_status(self, status: str) -> dict[str, WorkflowInstance]:
        """Get all workflows with a specific status.

        Args:
            status: The status to filter by

        Returns:
            Dictionary of workflow instances with the specified status
        """
        return {
            instance_id: workflow
            for instance_id, workflow in self._instances.items()
            if self._workflow_status.get(instance_id) == status
        }

    def get_available_workflows(self) -> dict[str, WorkflowInstance]:
        """Get all available workflows.

        Returns:
            Dictionary of available workflow instances
        """
        return {
            instance_id: workflow
            for instance_id, workflow in self._instances.items()
            if self._workflow_status.get(instance_id) in ["created", "ready", "running"]
        }

    def add_execution_history(self, instance_id: str, execution_data: dict[str, Any]) -> bool:
        """Add execution history entry for a workflow.

        Args:
            instance_id: The workflow instance ID
            execution_data: Execution data to record

        Returns:
            True if the workflow exists and history was added, False otherwise
        """
        if instance_id not in self._instances:
            return False
        if instance_id not in self._workflow_execution_history:
            self._workflow_execution_history[instance_id] = []
        self._workflow_execution_history[instance_id].append(execution_data)
        return True

    def get_execution_history(self, instance_id: str) -> list[dict[str, Any]]:
        """Get execution history for a workflow.

        Args:
            instance_id: The workflow instance ID

        Returns:
            List of execution history entries
        """
        return self._workflow_execution_history.get(instance_id, [])

    def get_workflow_metadata_for_llm(self, instance_id: str) -> dict[str, Any] | None:
        """Get LLM-friendly metadata from WorkflowInstance.

        Args:
            instance_id: The workflow instance ID

        Returns:
            Dictionary of metadata suitable for LLM decision-making, or None if not found
        """
        workflow = self._instances.get(instance_id)
        if not workflow:
            return None

        # Extract metadata from the WorkflowInstance's built-in fields
        metadata = {
            "instance_id": instance_id,
            "name": getattr(workflow, "name", ""),
            "workflow_type": self._workflow_types.get(instance_id, ""),
            "status": self._workflow_status.get(instance_id, "unknown"),
            "dependencies": self._workflow_dependencies.get(instance_id, []),
            "execution_history_count": len(self._workflow_execution_history.get(instance_id, [])),
        }

        # Add built-in metadata from WorkflowInstance
        if hasattr(workflow, "metadata"):
            metadata["builtin_metadata"] = workflow.metadata
        if hasattr(workflow, "_type"):
            metadata["docstring"] = workflow._type.docstring
            metadata["field_comments"] = workflow._type.field_comments
            metadata["fields"] = workflow._type.fields

        return metadata

    def match_workflow_for_llm(self, query: str, context: dict[str, Any]) -> tuple[float, WorkflowInstance | None, dict[str, Any] | None]:
        """Match workflow for LLM decision-making.

        Args:
            query: The search query
            context: Context entities for matching

        Returns:
            Tuple of (confidence_score, WorkflowInstance or None, metadata or None)
        """
        query_lower = query.lower()
        best_score = 0.0
        best_workflow = None
        best_metadata = None

        for instance_id, workflow in self._instances.items():
            metadata = self.get_workflow_metadata_for_llm(instance_id)
            if not metadata:
                continue

            # Calculate match score based on name, type, and metadata
            score = 0.0

            # Match by name
            if metadata.get("name", "").lower() in query_lower:
                score += 0.8

            # Match by workflow type
            if metadata.get("workflow_type", "").lower() in query_lower:
                score += 0.6

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
                best_workflow = workflow
                best_metadata = metadata

        return best_score, best_workflow, best_metadata

    def clear(self) -> None:
        """Clear all workflows and their metadata."""
        super().clear()
        self._workflow_types.clear()
        self._workflow_status.clear()
        self._workflow_execution_history.clear()
        self._workflow_dependencies.clear()
