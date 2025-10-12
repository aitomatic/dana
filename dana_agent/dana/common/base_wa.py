"""
Common functionality for first-class types above Resource: Agent, Workflow.
"""

from .base_war import BaseWAR
from .protocols import WorkflowProtocol


class BaseWA(BaseWAR):
    """Base class for Agents and Workflows with common functionality."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._workflows: list[WorkflowProtocol] = kwargs.get("workflows") or []

    def with_workflows(self, *workflows: WorkflowProtocol) -> "BaseWA":
        """Add workflows to the agent or workflow."""
        if workflows and len(workflows) > 0:
            for workflow in workflows:
                if workflow not in self._workflows:
                    self._workflows.append(workflow)
        return self

    def add_workflow(self, workflow: WorkflowProtocol) -> None:
        """
        Add a single workflow to the object.

        Args:
            workflow: WorkflowProtocol instance to add
        """
        if workflow not in self._workflows:
            self._workflows.append(workflow)

    def remove_workflow(self, workflow_id: str) -> bool:
        """
        Remove a workflow by its ID.

        Args:
            workflow_id: ID of the workflow to remove

        Returns:
            True if workflow was found and removed, False otherwise
        """
        for i, workflow in enumerate(self._workflows):
            if workflow.object_id == workflow_id:
                self._workflows.pop(i)
                return True
        return False
