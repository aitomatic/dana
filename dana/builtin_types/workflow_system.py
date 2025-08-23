"""
Workflow System for Dana

Specialized workflow type system with default fields and workflow-specific functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.builtin_types.fsm_system import create_fsm_struct_type, create_simple_workflow_fsm
from dana.builtin_types.struct_system import StructInstance, StructType


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

        # Initialize execution engine
        self._execution_engine = WorkflowExecutionEngine()

    @staticmethod
    def get_default_workflow_fields() -> dict[str, dict[str, Any]]:
        """Get the default fields that all workflows should have.

        This method defines what the standard workflow fields are,
        keeping the definition close to where they're used.
        """
        return {
            "name": {
                "type": "str",
                "default": "A Workflow",
                "comment": "Name of the workflow",
            },
            "fsm": {
                "type": "FSM | None",
                "default": None,  # Will be set to FSM instance during workflow creation
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

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute workflow with data.

        Args:
            data: Execution data including parameters and resources

        Returns:
            Dict[str, Any]: Execution result
        """
        return self._execute_workflow(data)

    def validate(self, data: dict[str, Any]) -> bool:
        """
        Validate input data for workflow execution.

        Args:
            data: Data to validate

        Returns:
            bool: True if data is valid
        """
        return self._validate_data(data)

    def get_status(self) -> str:
        """
        Get current execution status.

        Returns:
            str: Current status ("created", "executing", "completed", "error")
        """
        return self._execution_state

    @property
    def name(self) -> str:
        """
        Get the name of the workflow.

        Returns:
            str: Workflow name
        """
        return self.struct_type.name

    def get_history(self) -> list:
        """
        Get execution history.

        Returns:
            list: List of execution steps
        """
        return self._execution_history.copy()

    # Private implementation methods
    def _execute_workflow(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Private workflow execution implementation.

        Uses Dana's FSM system and execution engine to run the workflow.
        """
        try:
            # Update execution state
            self._execution_state = "executing"
            self._execution_history.append({"step": "start", "timestamp": self._get_timestamp(), "data": data})

            # Validate input data
            if not self.validate(data):
                raise ValueError("Invalid input data for workflow execution")

            # Execute using Dana's FSM system
            if hasattr(self, "fsm") and self.fsm:
                result = self._execution_engine.execute_fsm(self.fsm, data)
            else:
                # Fallback to simple execution
                result = self._execute_simple_workflow(data)

            # Update execution state
            self._execution_state = "completed"
            self._execution_history.append({"step": "complete", "timestamp": self._get_timestamp(), "result": result})

            return result

        except Exception as e:
            # Update execution state
            self._execution_state = "error"
            self._execution_history.append({"step": "error", "timestamp": self._get_timestamp(), "error": str(e)})

            return {"error": str(e), "status": "failed", "workflow_type": self.struct_type.name}

    def _validate_data(self, data: dict[str, Any]) -> bool:
        """
        Private data validation implementation.

        Validates data against workflow type requirements.
        """
        try:
            # Check if data contains required fields
            required_fields = ["problem"]
            for field in required_fields:
                if field not in data:
                    return False

            # Validate problem description
            if not isinstance(data["problem"], str) or not data["problem"].strip():
                return False

            # Validate parameters (optional)
            if "parameters" in data and not isinstance(data["parameters"], dict):
                return False

            # Validate resources (optional)
            if "resources" in data and not isinstance(data["resources"], list):
                return False

            return True

        except Exception:
            return False

    def _execute_simple_workflow(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute simple workflow without FSM.

        Provides basic execution for workflows that don't have FSM defined.
        """
        problem = data.get("problem", "")
        params = data.get("parameters", {})
        resources = data.get("resources", [])

        # Execute based on workflow type
        if self.struct_type.name == "EquipmentStatusWorkflow":
            return self._execute_equipment_status_workflow(problem, params, resources)
        elif self.struct_type.name == "DataAnalysisWorkflow":
            return self._execute_data_analysis_workflow(problem, params, resources)
        elif self.struct_type.name == "HealthCheckWorkflow":
            return self._execute_health_check_workflow(problem, params, resources)
        elif self.struct_type.name == "PipelineWorkflow":
            return self._execute_pipeline_workflow(problem, params, resources)
        else:
            # Generic workflow execution
            return self._execute_generic_workflow(problem, params, resources)

    def _execute_equipment_status_workflow(self, problem: str, params: dict[str, Any], resources: list) -> dict[str, Any]:
        """Execute equipment status workflow."""
        # Extract equipment ID from problem or params
        equipment_id = params.get("equipment_id", "Line 3")

        # Simulate equipment status check
        import datetime

        current_time = datetime.datetime.now().isoformat()

        return {
            "status": "operational",
            "temperature": 45.2,
            "last_check": current_time,
            "equipment_id": equipment_id,
            "workflow_type": "EquipmentStatusWorkflow",
        }

    def _execute_data_analysis_workflow(self, problem: str, params: dict[str, Any], resources: list) -> dict[str, Any]:
        """Execute data analysis workflow."""
        # Extract data source from problem or params
        data_source = params.get("data_source", "sensors.csv")

        # Simulate data analysis
        return {"mean_temp": 42.1, "max_temp": 67.8, "anomalies": 3, "data_source": data_source, "workflow_type": "DataAnalysisWorkflow"}

    def _execute_health_check_workflow(self, problem: str, params: dict[str, Any], resources: list) -> dict[str, Any]:
        """Execute health check workflow."""
        # Extract equipment ID from problem or params
        equipment_id = params.get("equipment_id", "Line 3")

        # Simulate health check
        return {
            "health": "good",
            "issues": [],
            "recommendations": ["schedule maintenance in 2 weeks"],
            "equipment_id": equipment_id,
            "workflow_type": "HealthCheckWorkflow",
        }

    def _execute_pipeline_workflow(self, problem: str, params: dict[str, Any], resources: list) -> dict[str, Any]:
        """Execute pipeline workflow."""
        # Extract data file from problem or params
        data_file = params.get("data_file", "sensors.csv")

        # Simulate pipeline execution
        return {
            "processed": True,
            "anomalies_found": 2,
            "output_file": "analysis_results.json",
            "data_file": data_file,
            "workflow_type": "PipelineWorkflow",
        }

    def _execute_generic_workflow(self, problem: str, params: dict[str, Any], resources: list) -> dict[str, Any]:
        """Execute generic workflow."""
        return {
            "status": "completed",
            "problem": problem,
            "params": params,
            "resources_used": len(resources),
            "workflow_type": self.struct_type.name,
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp for execution history."""
        import datetime

        return datetime.datetime.now().isoformat()


class WorkflowExecutionEngine:
    """
    Workflow execution engine that integrates with Dana's FSM system.

    Provides execution capabilities for workflows using Dana's existing FSM
    system and handles both FSM-based and simple workflow execution.
    """

    def __init__(self):
        """Initialize workflow execution engine."""
        pass

    def execute_fsm(self, fsm: Any, data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute workflow using Dana's FSM system.

        Args:
            fsm: Dana FSM instance
            data: Execution data

        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            # Use Dana's FSM execution if available
            if hasattr(fsm, "execute"):
                return fsm.execute(data)
            elif hasattr(fsm, "transition"):
                # Use FSM transition system
                return self._execute_fsm_transitions(fsm, data)
            else:
                # Fallback to simple execution
                return {"status": "completed", "fsm_used": True}

        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _execute_fsm_transitions(self, fsm: Any, data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute FSM using transition system.

        Args:
            fsm: Dana FSM instance
            data: Execution data

        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            # Get initial state
            current_state = fsm.current_state if hasattr(fsm, "current_state") else "start"

            # Execute transitions
            while current_state and current_state != "end":
                # Get next state
                next_state = fsm.transition(current_state, data)
                current_state = next_state

            return {"status": "completed", "final_state": current_state}

        except Exception as e:
            return {"error": str(e), "status": "failed"}


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
        field_defaults=field_defaults if field_defaults else {},
        field_comments=field_comments if field_comments else {},
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
