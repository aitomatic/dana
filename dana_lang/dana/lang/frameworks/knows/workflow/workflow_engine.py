"""
Workflow Engine - Main orchestration engine for Dana Workflows.

This module provides the core workflow orchestration capabilities built on top of
Dana's existing composition framework. It enables hierarchical deterministic control
with workflows "all the way down" while maintaining enterprise safety standards.

Key Features:
- Hierarchical workflow composition using Dana's | operator
- Deterministic execution with safety validation
- Context-aware step execution
- Integration with POET framework for runtime objectives
- Enterprise-grade error handling and logging
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .context_engine import ContextEngine
from .safety_validator import SafetyValidator
from .workflow_step import WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class WorkflowExecutionContext:
    """Context object passed through workflow execution."""

    workflow_id: str
    step_id: str
    input_data: Any
    context_data: dict[str, Any] = field(default_factory=dict)
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    safety_flags: list[str] = field(default_factory=list)

    def add_context(self, key: str, value: Any) -> None:
        """Add context data for downstream steps."""
        self.context_data[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context data from upstream steps."""
        return self.context_data.get(key, default)


class WorkflowEngine:
    """
    Main workflow orchestration engine.

    Provides hierarchical deterministic control over workflow execution while
    maintaining safety and compliance standards.
    """

    def __init__(self, context_engine: ContextEngine | None = None, safety_validator: SafetyValidator | None = None, max_depth: int = 10):
        """
        Initialize the workflow engine.

        Args:
            context_engine: Context engine for knowledge curation
            safety_validator: Safety validator for enterprise compliance
            max_depth: Maximum nesting depth for hierarchical workflows
        """
        self.context_engine = context_engine or ContextEngine()
        self.safety_validator = safety_validator or SafetyValidator()
        self.max_depth = max_depth
        self.active_workflows: dict[str, dict[str, Any]] = {}

        logger.info(f"Initialized WorkflowEngine with max_depth={max_depth}")

    def execute(
        self,
        workflow: list[WorkflowStep] | Callable,
        input_data: Any,
        workflow_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """
        Execute a workflow with full orchestration support.

        Args:
            workflow: Either a list of WorkflowStep objects or a composed function
            input_data: Initial input data for the workflow
            workflow_id: Optional identifier for tracking
            metadata: Optional execution metadata

        Returns:
            Workflow execution result

        Raises:
            ValueError: If workflow is invalid
            RuntimeError: If execution fails
            SafetyError: If safety validation fails
        """
        workflow_id = workflow_id or f"workflow_{id(workflow)}"
        metadata = metadata or {}

        logger.info(f"Starting workflow execution: {workflow_id}")

        # Initialize execution context
        context = WorkflowExecutionContext(workflow_id=workflow_id, step_id="root", input_data=input_data, execution_metadata=metadata)

        try:
            # Validate workflow
            self._validate_workflow(workflow)

            # Pre-execution safety check
            safety_result = self.safety_validator.validate_workflow(workflow, context)
            if not safety_result.is_safe:
                logger.error(f"Safety validation failed for workflow {workflow_id}")
                raise RuntimeError(f"Safety validation failed: {safety_result.reason}")

            # Execute workflow
            if isinstance(workflow, list):
                result = self._execute_step_list(workflow, input_data, context)
            else:
                # Assume it's a composed function (using Dana's | operator)
                result = self._execute_composed_function(workflow, input_data, context)

            # Post-execution processing
            self._post_execution_processing(context, result)

            logger.info(f"Workflow {workflow_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            self._handle_execution_error(context, e)
            raise

    def _validate_workflow(self, workflow: Any) -> None:
        """Validate workflow structure."""
        if isinstance(workflow, list):
            if not all(isinstance(step, WorkflowStep) for step in workflow):
                raise ValueError("All steps must be WorkflowStep instances")
        elif not callable(workflow):
            raise ValueError("Workflow must be either a list of steps or a callable")

    def _execute_step_list(self, steps: list[WorkflowStep], input_data: Any, context: WorkflowExecutionContext) -> Any:
        """Execute a list of workflow steps in sequence."""
        current_data = input_data

        for i, step in enumerate(steps):
            step_context = WorkflowExecutionContext(
                workflow_id=context.workflow_id,
                step_id=f"step_{i}_{step.name}",
                input_data=current_data,
                context_data=context.context_data.copy(),
                execution_metadata=context.execution_metadata,
            )

            logger.debug(f"Executing step {i + 1}/{len(steps)}: {step.name}")

            # Step-level safety validation
            step_safety = self.safety_validator.validate_step(step, step_context)
            if not step_safety.is_safe:
                logger.error(f"Step safety validation failed: {step.name}")
                raise RuntimeError(f"Step validation failed: {step_safety.reason}")

            # Execute step
            try:
                current_data = step.execute(current_data, step_context)

                # Update context for downstream steps
                context.add_context(f"step_{i}_result", current_data)

            except Exception as e:
                logger.error(f"Step execution failed: {step.name} - {str(e)}")
                if step.error_handler:
                    current_data = step.error_handler(e, step_context)
                else:
                    raise

        return current_data

    def _execute_composed_function(self, composed_func: Callable, input_data: Any, context: WorkflowExecutionContext) -> Any:
        """Execute a composed function using Dana's existing | operator."""
        logger.debug("Executing composed function via Dana pipeline")

        # For composed functions, we rely on Dana's existing composition
        # Context is passed implicitly through the execution
        try:
            return composed_func(input_data)
        except Exception as e:
            logger.error(f"Composed function execution failed: {str(e)}")
            raise

    def _post_execution_processing(self, context: WorkflowExecutionContext, result: Any) -> None:
        """Post-execution processing and cleanup."""
        # Update context with final result
        context.add_context("final_result", result)

        # Log execution summary
        logger.info(f"Workflow {context.workflow_id} completed with result type: {type(result)}")

        # Cleanup if needed
        if context.workflow_id in self.active_workflows:
            del self.active_workflows[context.workflow_id]

    def _handle_execution_error(self, context: WorkflowExecutionContext, error: Exception) -> None:
        """Handle workflow execution errors."""
        logger.error(f"Workflow execution error in {context.workflow_id}: {str(error)}")

        # Log error context
        error_context = {
            "workflow_id": context.workflow_id,
            "step_id": context.step_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "input_type": type(context.input_data).__name__,
        }

        logger.error(f"Error context: {error_context}")

        # Cleanup
        if context.workflow_id in self.active_workflows:
            del self.active_workflows[context.workflow_id]

    def create_workflow_step(
        self,
        name: str,
        function: Callable,
        pre_conditions: list[Callable] | None = None,
        post_conditions: list[Callable] | None = None,
        error_handler: Callable | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStep:
        """
        Create a new workflow step with integrated safety and context support.

        Args:
            name: Step name for identification
            function: The function to execute
            pre_conditions: List of pre-execution conditions
            post_conditions: List of post-execution conditions
            error_handler: Error handling function
            metadata: Additional step metadata

        Returns:
            Configured WorkflowStep instance
        """
        return WorkflowStep(
            name=name,
            function=function,
            pre_conditions=pre_conditions or [],
            post_conditions=post_conditions or [],
            error_handler=error_handler,
            metadata=metadata or {},
        )
