"""
Workflow System for Dana

Simplified workflow system that compiles to ComposedFunction for seamless integration
with Dana's function composition system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.builtin_types.struct_system import StructInstance, StructType
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext

ProblemContext = dict[str, Any]


@dataclass
class WorkflowType(StructType):
    """Workflow struct type with minimal workflow capabilities.

    Inherits from StructType and adds basic workflow functionality.
    """

    @staticmethod
    def get_default_workflow_fields() -> dict[str, dict[str, Any]]:
        """Get the default fields that all workflows should have."""
        return {
            "name": {
                "type": "str",
                "default": "A Workflow",
                "comment": "Name of the workflow",
            },
            "composed_function": {
                "type": "ComposedFunction | None",
                "default": None,
                "comment": "The composed function that implements the workflow",
            },
            "metadata": {
                "type": "dict",
                "default": {},
                "comment": "Additional workflow metadata",
            },
        }

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
        additional_fields = self.get_default_workflow_fields()

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


class WorkflowInstance(StructInstance):
    """Workflow struct instance that wraps a ComposedFunction.

    This simplified workflow system directly uses Dana's function composition
    system for execution.
    """

    def __init__(self, struct_type: WorkflowType, values: dict[str, Any], parent_workflow: "WorkflowInstance | None" = None):
        """Create a new workflow struct instance.

        Args:
            struct_type: The workflow struct type definition
            values: Field values (must match struct type requirements)
            parent_workflow: Parent workflow instance for recursive calls
        """
        # Ensure we have a WorkflowType
        if not isinstance(struct_type, WorkflowType):
            raise TypeError(f"WorkflowInstance requires WorkflowType, got {type(struct_type)}")

        # Initialize workflow-specific state
        self._execution_history = []
        self._composed_function = None
        self._parent_workflow = parent_workflow
        self._children = []

        # Initialize workflow-specific state
        self._execution_history = []
        self._composed_function = None
        self._parent_workflow = parent_workflow
        self._children = []

        # Initialize the base StructInstance
        super().__init__(struct_type, values, None)

        # Extract composed function from values if provided
        if "composed_function" in values:
            self._composed_function = values["composed_function"]

        # Link to parent if provided
        if parent_workflow:
            parent_workflow._children.append(self)

    def set_composed_function(self, composed_function: SandboxFunction) -> None:
        """Set the composed function for this workflow."""
        self._composed_function = composed_function

    def get_composed_function(self) -> SandboxFunction | None:
        """Get the composed function for this workflow."""
        return self._composed_function

    def get_root_workflow(self) -> "WorkflowInstance":
        """Navigate to root workflow."""
        current = self
        while current._parent_workflow:
            current = current._parent_workflow
        return current

    def get_sibling_workflows(self) -> list["WorkflowInstance"]:
        """Get workflows at same level."""
        if not self._parent_workflow:
            return []
        return [w for w in self._parent_workflow._children if w != self]

    def get_ancestor_context(self, levels_up: int) -> Any:
        """Get context from ancestor workflow (simplified version)."""
        current = self
        for _ in range(levels_up):
            if current._parent_workflow:
                current = current._parent_workflow
            else:
                break
        # In simplified design, no problem_context available
        return None

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get the execution history of the workflow."""
        return self._execution_history.copy()

    def add_execution_step(self, step: dict[str, Any]) -> None:
        """Add an execution step to the history."""
        self._execution_history.append(step)

    def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the workflow using the composed function.

        Args:
            context: The execution context
            *args: Positional arguments to pass to the workflow
            **kwargs: Keyword arguments to pass to the workflow

        Returns:
            The result of workflow execution

        Raises:
            RuntimeError: If no composed function set
        """
        if not self._composed_function:
            raise RuntimeError("No composed function set for this workflow")

        # Set up execution context
        context.workflow_instance = self

        # Record execution start
        import time

        start_time = time.time()

        # Add execution step to history
        self.add_execution_step({"step": "start", "timestamp": start_time, "status": "executing"})

        try:
            # Execute the composed function - handle both ComposedFunction and regular callables
            if hasattr(self._composed_function, "execute"):
                # It's a ComposedFunction or similar object with execute method
                result = self._composed_function.execute(context, *args, **kwargs)
            else:
                # It's a regular callable function
                result = self._composed_function(*args, **kwargs)

            # Record successful completion
            execution_time = time.time() - start_time
            self.add_execution_step(
                {"step": "complete", "timestamp": time.time(), "status": "completed", "execution_time": execution_time, "result": result}
            )

            return result

        except Exception as e:
            # Record error
            execution_time = time.time() - start_time
            self.add_execution_step(
                {"step": "error", "timestamp": time.time(), "status": "error", "execution_time": execution_time, "error": str(e)}
            )
            raise e

    def get_status(self) -> str:
        """
        Get current execution status based on execution history.

        Returns:
            str: Current status ("ready", "executing", "completed", "error")
        """
        if not self._execution_history:
            return "ready"

        last_step = self._execution_history[-1]
        step_name = last_step.get("step", "")

        if step_name == "error":
            return "error"
        elif step_name == "complete":
            return "completed"
        elif step_name == "start":
            return "executing"
        else:
            return "ready"

    @property
    def name(self) -> str:
        """Get the name of the workflow."""
        return self.struct_type.name

    def get_history(self) -> list[dict[str, Any]]:
        """Get execution history."""
        return self.get_execution_history()

    def _get_timestamp(self) -> str:
        """Get current timestamp for execution history."""
        import datetime

        return datetime.datetime.now().isoformat()


# Factory functions for creating workflows


def create_workflow_from_composed_function(
    name: str, composed_function: SandboxFunction, metadata: dict[str, Any] | None = None
) -> WorkflowInstance:
    """
    Create a workflow from a ComposedFunction.

    Args:
        name: Name of the workflow
        composed_function: The composed function to execute
        metadata: Optional metadata for the workflow

    Returns:
        WorkflowInstance with the composed function
    """
    # Create workflow type with default fields
    workflow_type = WorkflowType(name=name, fields={}, field_order=[], docstring=f"Workflow: {name}")

    # Create workflow instance
    workflow = WorkflowInstance(
        workflow_type,
        {
            "name": name,
            "composed_function": composed_function,
            "metadata": metadata or {},
        },
    )

    return workflow


# Legacy support functions (for backward compatibility)


def create_workflow_from_dana_code(
    name: str, dana_code: str, context: SandboxContext, metadata: dict[str, Any] | None = None
) -> WorkflowInstance:
    """
    Create a workflow by parsing Dana code directly.

    Args:
        name: Name of the workflow
        dana_code: Dana pipeline expression as a string
        context: SandboxContext with parser and interpreter
        metadata: Optional metadata for the workflow

    Returns:
        WorkflowInstance with parsed ComposedFunction
    """
    # Parse Dana code using the context's parser
    ast = context.parser.parse_expression(dana_code)

    # Execute AST to get ComposedFunction using the context's interpreter
    composed_function = context.interpreter.evaluate_expression(ast, context)

    # Create workflow instance
    workflow = create_workflow_from_composed_function(
        name=name,
        composed_function=composed_function,
        metadata={"dana_code": dana_code, "source": "dana_code", **(metadata or {})},
    )

    return workflow
