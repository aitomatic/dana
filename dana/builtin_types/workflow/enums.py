"""
Workflow System Enums.

This module defines enums specific to the workflow and FSM systems.
These enums are used for workflow execution states and FSM transition events.
"""

from enum import Enum


class WorkflowExecutionState(Enum):
    """Enum for workflow execution states."""

    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"

    def __str__(self) -> str:
        return self.value


class FSMTransitionEvent(Enum):
    """Enum for FSM transition events."""

    START = "START"
    NEXT = "NEXT"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    COMPLETE = "COMPLETE"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"

    def __str__(self) -> str:
        return self.value
