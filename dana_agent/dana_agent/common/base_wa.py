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
