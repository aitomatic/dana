"""
Workflow Step - Individual step abstraction for agentic workflows.

This module provides the WorkflowStep class, which represents a single step
in an agentic workflow. Each step encapsulates a function with safety checks,
context management, and error handling.

Key Features:
- Encapsulated step execution with safety validation
- Context-aware function execution
- Pre/post condition checking
- Error handling and recovery
- Metadata support for enterprise tracking
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of a workflow step execution."""

    data: Any
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Exception | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StepExecutionContext:
    """Context for step execution."""

    step_id: str
    workflow_id: str
    input_data: Any
    previous_steps: dict[str, Any] = field(default_factory=dict)
    global_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowStep:
    """
    Individual workflow step with safety and context support.

    Represents a single step in an agentic workflow that can be composed
    using Dana's existing | operator. Each step encapsulates a function
    with additional safety, validation, and context management features.
    """

    def __init__(
        self,
        name: str,
        function: Callable,
        pre_conditions: list[Callable] | None = None,
        post_conditions: list[Callable] | None = None,
        error_handler: Callable | None = None,
        metadata: dict[str, Any] | None = None,
        timeout: float | None = None,
    ):
        """
        Initialize a workflow step.

        Args:
            name: Step name for identification and logging
            function: The function to execute for this step
            pre_conditions: List of pre-execution validation functions
            post_conditions: List of post-execution validation functions
            error_handler: Function to handle step execution errors
            metadata: Additional step metadata
            timeout: Optional timeout in seconds
        """
        self.name = name
        self.function = function
        self.pre_conditions = pre_conditions or []
        self.post_conditions = post_conditions or []
        self.error_handler = error_handler
        self.metadata = metadata or {}
        self.timeout = timeout

        logger.debug(f"Initialized workflow step: {name}")

    def execute(self, input_data: Any, context: Any = None) -> Any:
        """
        Execute this workflow step with full validation and error handling.

        Args:
            input_data: Input data for the step
            context: Optional execution context

        Returns:
            Step execution result

        Raises:
            RuntimeError: If step execution fails
            ValidationError: If pre/post conditions fail
        """
        logger.debug(f"Executing step: {self.name}")

        # Create step execution context
        step_context = self._create_step_context(input_data, context)

        try:
            # Pre-execution validation
            self._validate_pre_conditions(input_data, step_context)

            # Execute the step function
            result = self._execute_function(input_data, step_context)

            # Post-execution validation
            self._validate_post_conditions(result, step_context)

            logger.debug(f"Step {self.name} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Step {self.name} failed: {str(e)}")
            if self.error_handler:
                return self.error_handler(e, input_data, step_context)
            else:
                raise RuntimeError(f"Step {self.name} failed: {str(e)}") from e

    def _create_step_context(self, input_data: Any, context: Any = None) -> StepExecutionContext:
        """Create step execution context."""
        # Extract relevant context information
        workflow_id = getattr(context, "workflow_id", "unknown")
        step_id = f"{workflow_id}_{self.name}"

        # Build context data
        global_context = {}
        previous_steps = {}

        if context:
            if hasattr(context, "context_data"):
                global_context = context.context_data
            if hasattr(context, "execution_metadata"):
                previous_steps = context.execution_metadata

        return StepExecutionContext(
            step_id=step_id,
            workflow_id=workflow_id,
            input_data=input_data,
            global_context=global_context,
            previous_steps=previous_steps,
            metadata=self.metadata,
        )

    def _validate_pre_conditions(self, input_data: Any, context: StepExecutionContext) -> None:
        """Validate pre-execution conditions."""
        for condition in self.pre_conditions:
            try:
                if not condition(input_data, context):
                    raise ValueError(f"Pre-condition failed for step {self.name}")
            except Exception as e:
                logger.error(f"Pre-condition error in step {self.name}: {str(e)}")
                raise

    def _validate_post_conditions(self, result: Any, context: StepExecutionContext) -> None:
        """Validate post-execution conditions."""
        for condition in self.post_conditions:
            try:
                if not condition(result, context):
                    raise ValueError(f"Post-condition failed for step {self.name}")
            except Exception as e:
                logger.error(f"Post-condition error in step {self.name}: {str(e)}")
                raise

    def _execute_function(self, input_data: Any, context: StepExecutionContext) -> Any:
        """Execute the step function with optional timeout."""
        import signal

        def _timeout_handler(signum, frame):
            raise TimeoutError(f"Step {self.name} timed out after {self.timeout}s")

        if self.timeout:
            # Set up timeout handling
            if hasattr(signal, "SIGALRM"):
                # Unix-like systems
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(int(self.timeout))
                try:
                    result = self.function(input_data)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Windows or no SIGALRM support
                result = self.function(input_data)
        else:
            # No timeout
            result = self.function(input_data)

        return result

    def __or__(self, other: "WorkflowStep") -> Callable:
        """
        Enable composition using Dana's | operator.

        This allows workflow steps to be composed like:
        step1 | step2 | step3

        Args:
            other: Next workflow step

        Returns:
            Composed function ready for execution
        """

        def composed_function(input_data: Any) -> Any:
            """Execute steps in sequence."""
            first_result = self.execute(input_data)
            return other.execute(first_result)

        # Preserve step information for debugging
        composed_function.__name__ = f"{self.name}_then_{other.name}"
        composed_function._workflow_steps = [self, other]

        return composed_function

    def __repr__(self) -> str:
        """String representation of the workflow step."""
        return f"WorkflowStep(name='{self.name}', metadata={self.metadata})"

    def clone(self, **overrides) -> "WorkflowStep":
        """
        Create a copy of this step with optional overrides.

        Args:
            **overrides: Override any step attributes

        Returns:
            New WorkflowStep instance
        """
        kwargs = {
            "name": overrides.get("name", self.name),
            "function": overrides.get("function", self.function),
            "pre_conditions": overrides.get("pre_conditions", self.pre_conditions.copy()),
            "post_conditions": overrides.get("post_conditions", self.post_conditions.copy()),
            "error_handler": overrides.get("error_handler", self.error_handler),
            "metadata": overrides.get("metadata", self.metadata.copy()),
            "timeout": overrides.get("timeout", self.timeout),
        }

        return WorkflowStep(**kwargs)

    @classmethod
    def from_function(
        cls,
        name: str | None = None,
        pre_conditions: list[Callable] | None = None,
        post_conditions: list[Callable] | None = None,
        error_handler: Callable | None = None,
        metadata: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Callable:
        """
        Decorator to convert a regular function into a WorkflowStep.

        Args:
            name: Optional step name (defaults to function name)
            pre_conditions: List of pre-execution conditions
            post_conditions: List of post-execution conditions
            error_handler: Error handling function
            metadata: Additional step metadata
            timeout: Optional timeout in seconds

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> "WorkflowStep":
            step_name = name or func.__name__
            return cls(
                name=step_name,
                function=func,
                pre_conditions=pre_conditions,
                post_conditions=post_conditions,
                error_handler=error_handler,
                metadata=metadata,
                timeout=timeout,
            )

        return decorator
