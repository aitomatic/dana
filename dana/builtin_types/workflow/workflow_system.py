"""
Workflow System for Dana

Specialized workflow type system with default fields and workflow-specific functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.builtin_types.fsm_system import create_fsm_struct_type, create_simple_workflow_fsm
from dana.builtin_types.struct_system import StructInstance, StructType
from dana.core.lang.sandbox_context import SandboxContext


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

    def execute(self, agent_instance: AgentInstance, data: dict[str, Any], sandbox_context: SandboxContext | None = None) -> dict[str, Any]:
        """
        Execute workflow with data.

        Args:
            data: Execution data including parameters and resources

        Returns:
            Dict[str, Any]: Execution result
        """
        return self._execute_workflow(agent_instance, data, sandbox_context)

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
    def _execute_workflow(
        self, agent_instance: AgentInstance, data: dict[str, Any], sandbox_context: SandboxContext | None = None
    ) -> dict[str, Any]:
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
                result = self._execution_engine.execute_fsm(agent_instance, self.fsm, data, sandbox_context)
            else:
                # Fallback to simple execution
                result = self._execute_simple_workflow(agent_instance, data, sandbox_context)

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

    def _execute_simple_workflow(
        self, agent_instance: AgentInstance, data: dict[str, Any], sandbox_context: SandboxContext | None = None
    ) -> dict[str, Any]:
        """
        Execute simple workflow without FSM.

        Provides basic execution for workflows that don't have FSM defined.
        """
        problem = data.get("problem", "")
        params = data.get("parameters", {})
        resources = data.get("resources", [])

        # Execute based on workflow type
        if self.struct_type.name == "EquipmentStatusWorkflow":
            return self._execute_equipment_status_workflow(agent_instance, problem, params, resources, sandbox_context)
        elif self.struct_type.name == "DataAnalysisWorkflow":
            return self._execute_data_analysis_workflow(agent_instance, problem, params, resources, sandbox_context)
        elif self.struct_type.name == "HealthCheckWorkflow":
            return self._execute_health_check_workflow(agent_instance, problem, params, resources, sandbox_context)
        elif self.struct_type.name == "PipelineWorkflow":
            return self._execute_pipeline_workflow(agent_instance, problem, params, resources, sandbox_context)
        else:
            # Generic workflow execution
            return self._execute_generic_workflow(agent_instance, problem, params, resources, sandbox_context)

    def _execute_equipment_status_workflow(
        self,
        agent_instance: AgentInstance,
        problem: str,
        params: dict[str, Any],
        resources: list,
        sandbox_context: SandboxContext | None = None,
    ) -> dict[str, Any]:
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

    def _execute_data_analysis_workflow(
        self,
        agent_instance: AgentInstance,
        problem: str,
        params: dict[str, Any],
        resources: list,
        sandbox_context: SandboxContext | None = None,
    ) -> dict[str, Any]:
        """Execute data analysis workflow."""
        # Extract data source from problem or params
        data_source = params.get("data_source", "sensors.csv")

        # Simulate data analysis
        return {"mean_temp": 42.1, "max_temp": 67.8, "anomalies": 3, "data_source": data_source, "workflow_type": "DataAnalysisWorkflow"}

    def _execute_health_check_workflow(
        self,
        agent_instance: AgentInstance,
        problem: str,
        params: dict[str, Any],
        resources: list,
        sandbox_context: SandboxContext | None = None,
    ) -> dict[str, Any]:
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

    def _execute_pipeline_workflow(
        self,
        agent_instance: AgentInstance,
        problem: str,
        params: dict[str, Any],
        resources: list,
        sandbox_context: SandboxContext | None = None,
    ) -> dict[str, Any]:
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

    def _execute_generic_workflow(
        self,
        agent_instance: AgentInstance,
        problem: str,
        params: dict[str, Any],
        resources: list,
        sandbox_context: SandboxContext | None = None,
    ) -> dict[str, Any]:
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
    Workflow execution engine that integrates with Dana's enhanced FSM system.

    Provides execution capabilities for workflows using the enhanced FSM
    structure with state metadata, results, and workflow metadata.
    """

    def __init__(self):
        """Initialize workflow execution engine."""
        pass

    def execute_fsm(
        self, agent_instance: AgentInstance, fsm: Any, data: dict[str, Any], sandbox_context: SandboxContext | None = None
    ) -> dict[str, Any]:
        """
        Execute workflow using Dana's enhanced FSM system.

        Args:
            fsm: Dana FSM instance with enhanced structure
            data: Execution data

        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            # Use enhanced FSM execution
            return self._execute_enhanced_fsm(agent_instance, fsm, data, sandbox_context)

        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _execute_enhanced_fsm(
        self, agent_instance: AgentInstance, fsm: Any, data: dict[str, Any], sandbox_context: SandboxContext | None = None
    ) -> dict[str, Any]:
        """
        Execute enhanced FSM with state metadata and results.

        Args:
            fsm: Dana FSM instance with enhanced structure
            data: Execution data

        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            from dana.builtin_types.fsm_system import (
                get_current_state_action,
                get_current_state_metadata,
                get_current_state_objective,
                get_current_state_parameters,
                set_state_result,
                transition_fsm,
                update_state_status,
            )

            # Initialize execution
            current_state = fsm.current_state
            execution_results = {}

            # Execute workflow through FSM states
            while current_state and current_state not in ["COMPLETE", "ERROR"]:
                # Get current state metadata
                state_metadata = get_current_state_metadata(fsm)
                if not state_metadata:
                    # Skip states without metadata (like START, COMPLETE)
                    if transition_fsm(fsm, "next"):
                        current_state = fsm.current_state
                        continue
                    else:
                        break

                # Update state status to executing
                update_state_status(fsm, current_state, "executing")

                # Execute the action for current state
                action = get_current_state_action(fsm) or "execute_step"
                objective = get_current_state_objective(fsm) or "Execute workflow step"
                parameters = get_current_state_parameters(fsm)

                # Execute action (this would integrate with agent system)
                step_result = self._execute_state_action(agent_instance, action, objective, parameters, data, sandbox_context)

                # Store result
                set_state_result(fsm, current_state, step_result)
                execution_results[current_state] = step_result

                # Update state status to completed
                update_state_status(fsm, current_state, "completed")

                # Transition to next state
                if transition_fsm(fsm, "next"):
                    current_state = fsm.current_state
                else:
                    break

            # Return final results
            return {
                "status": "completed" if current_state == "COMPLETE" else "failed",
                "final_state": current_state,
                "results": execution_results,
                "fsm_results": fsm.results,
            }

        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _execute_state_action(
        self,
        agent_instance: AgentInstance,
        action: str,
        objective: str,
        parameters: dict,
        data: dict,
        sandbox_context: SandboxContext | None = None,
    ) -> dict:
        """
        Execute a state action (placeholder for agent integration).

        Args:
            action: Action to execute
            objective: Objective of the action
            parameters: Action parameters
            data: Execution data

        Returns:
            Dict: Action execution result
        """
        agent_instance.debug(f"EXECUTE_STATE_ACTION: Executing action: {action} with objective: {objective}")
        agent_instance.debug(f"EXECUTE_STATE_ACTION: Parameters: {parameters}")
        agent_instance.debug(f"EXECUTE_STATE_ACTION: Data: {data}")

        if isinstance(parameters, dict) and isinstance(data, dict):
            data["fsm_parameters"] = parameters

        result = agent_instance.solve(f"Execute action: {action} with objective: {objective}", data, sandbox_context=sandbox_context)
        agent_instance.debug(f"EXECUTE_STATE_ACTION: Action result: {result}")

        return result
        """
        return {
            "action": action,
            "objective": objective,
            "parameters": parameters,
            "status": "executed",
            "result": f"Executed {action} with objective: {objective}",
        }
        """


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
        field_defaults=field_defaults or {},
        field_comments=field_comments or {},
        docstring=workflow_def.docstring,
    )


def register_fsm_struct_type() -> None:
    """Register the FSM struct type in the global registry."""
    from dana.registry import TYPE_REGISTRY

    fsm_type = create_fsm_struct_type()
    TYPE_REGISTRY.register_struct_type(fsm_type)


def create_fsm_instance(fsm_data: dict[str, Any] | None = None) -> Any:
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
