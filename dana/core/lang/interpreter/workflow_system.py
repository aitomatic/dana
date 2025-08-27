"""
Workflow System for Dana

Specialized workflow type system with default fields and workflow-specific functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.core.builtin_types.fsm_system import create_fsm_struct_type, create_simple_workflow_fsm
from dana.core.builtin_types.struct_system import StructInstance, StructType


@dataclass
class WorkflowType(StructType):
    """Workflow struct type with built-in workflow capabilities.

    Inherits from StructType and adds workflow-specific functionality.
    """

    def __init__(
        self,
        name: str,
        fields: dict[str, str],
        field_order: list[str],
        field_comments: dict[str, str] | None = None,
        field_defaults: dict[str, Any] | None = None,
        docstring: str | None = None,
    ):
        """Initialize WorkflowType with default workflow fields."""
        # Add default workflow fields automatically
        additional_fields = WorkflowInstance.get_default_workflow_fields()

        # Merge additional fields into the provided fields
        merged_fields = fields.copy()
        merged_field_order = field_order.copy()
        merged_field_defaults = field_defaults.copy() if field_defaults else {}
        merged_field_comments = field_comments.copy() if field_comments else {}

        for field_name, field_info in additional_fields.items():
            if field_name not in merged_fields:
                merged_fields[field_name] = field_info["type"]
                merged_field_order.append(field_name)

                merged_field_defaults[field_name] = field_info["default"]

                merged_field_comments[field_name] = field_info["comment"]

        # Initialize as a regular StructType
        super().__init__(
            name=name,
            fields=merged_fields,
            field_order=merged_field_order,
            field_comments=merged_field_comments,
            field_defaults=merged_field_defaults,
            docstring=docstring,
        )

        # No need for custom validation override since FSM field is "FSM | None"


class WorkflowInstance(StructInstance):
    """Workflow struct instance with built-in workflow capabilities.

    Inherits from StructInstance and adds workflow-specific state and methods.
    """

    def __init__(self, struct_type: WorkflowType, values: dict[str, Any]):
        """Create a new workflow struct instance.

        Args:
            struct_type: The workflow struct type definition
            values: Field values (must match struct type requirements)
        """
        # Ensure we have a WorkflowType
        if not isinstance(struct_type, WorkflowType):
            raise TypeError(f"WorkflowInstance requires WorkflowType, got {type(struct_type)}")

        # Initialize workflow-specific state
        self._execution_state = "created"
        self._execution_history = []

        # Initialize the base StructInstance
        from dana.registry import WORKFLOW_REGISTRY

        super().__init__(struct_type, values, WORKFLOW_REGISTRY)

        # After initialization, ensure FSM field has a proper instance if it's None
        if hasattr(self, "fsm") and self.fsm is None:
            self.fsm = create_fsm_instance()

    @staticmethod
    def get_default_workflow_fields() -> dict[str, dict[str, Any]]:
        """Get the default fields that all workflows should have.

        This method defines what the standard workflow fields are,
        keeping the definition close to where they're used.
        """

        # Create a default FSM instance lazily
        def _get_default_fsm():
            try:
                return create_fsm_instance()
            except Exception:
                # Fallback to None if FSM creation fails
                return None

        return {
            "name": {
                "type": "str",
                "default": "A Workflow",
                "comment": "Name of the workflow",
            },
            "fsm": {
                "type": "FSM",
                "default": _get_default_fsm(),
                "comment": "Finite State Machine for workflow execution",
            },
        }

    def get_execution_state(self) -> str:
        """Get the current execution state of the workflow."""
        return self._execution_state

    def set_execution_state(self, state: str) -> None:
        """Set the current execution state of the workflow."""
        self._execution_state = state
        self._execution_history.append(state)

    def get_execution_history(self) -> list[str]:
        """Get the execution history of the workflow."""
        return self._execution_history.copy()


def create_workflow_type_from_ast(workflow_def) -> WorkflowType:
    """Create a WorkflowType from a WorkflowDefinition AST node.

    Args:
        workflow_def: The WorkflowDefinition AST node

    Returns:
        WorkflowType with fields and default values
    """
    from dana.core.lang.ast import WorkflowDefinition

    if not isinstance(workflow_def, WorkflowDefinition):
        raise TypeError(f"Expected WorkflowDefinition, got {type(workflow_def)}")

    # Convert StructField list to dict and field order
    fields = {}
    field_order = []
    field_defaults = {}
    field_comments = {}

    for field in workflow_def.fields:
        if field.type_hint is None:
            raise ValueError(f"Field {field.name} has no type hint")
        if not hasattr(field.type_hint, "name"):
            raise ValueError(f"Field {field.name} type hint {field.type_hint} has no name attribute")
        fields[field.name] = field.type_hint.name
        field_order.append(field.name)

        # Handle default value if present
        if field.default_value is not None:
            field_defaults[field.name] = field.default_value

        # Store field comment if present
        if field.comment:
            field_comments[field.name] = field.comment

    return WorkflowType(
        name=workflow_def.name,
        fields=fields,
        field_order=field_order,
        field_defaults=field_defaults if field_defaults else None,
        field_comments=field_comments,
        docstring=workflow_def.docstring,
    )


def register_fsm_struct_type() -> None:
    """Register the FSM struct type in the global registry."""
    from dana.registry import TYPE_REGISTRY

    fsm_type = create_fsm_struct_type()
    TYPE_REGISTRY.register_struct_type(fsm_type)


def create_fsm_instance(fsm_data: dict[str, Any] = None) -> Any:
    """Create an FSM struct instance.

    Args:
        fsm_data: FSM data dictionary, or None for default simple workflow FSM

    Returns:
        FSM struct instance
    """
    from dana.registry import TYPE_REGISTRY

    # Ensure FSM type is registered
    if not TYPE_REGISTRY.has_struct_type("FSM"):
        register_fsm_struct_type()

    # Use provided data or default simple workflow FSM
    if fsm_data is None:
        fsm_data = create_simple_workflow_fsm()

    # Create FSM instance
    return TYPE_REGISTRY.create_instance("FSM", fsm_data)
