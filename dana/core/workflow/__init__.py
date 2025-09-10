"""
Workflow System for Dana

This module provides simplified workflow capabilities that compile to ComposedFunction
for seamless integration with Dana's function composition system.
"""

from .workflow_system import (
    WorkflowInstance,
    WorkflowType,
    create_workflow_from_composed_function,
    create_workflow_from_dana_code,
)

__all__ = [
    "WorkflowType",
    "WorkflowInstance",
    "create_workflow_from_composed_function",
    "create_workflow_from_dana_code",
]
