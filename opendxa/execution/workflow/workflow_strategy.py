"""Workflow execution strategies."""

from enum import Enum

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN" 