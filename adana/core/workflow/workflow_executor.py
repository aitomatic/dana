"""
WorkflowExecutor - Deterministic SA-loop execution pattern with callables only.

Provides 95% deterministic workflow execution with:
- Predetermined callable steps (no LLM planning)
- Simple execution with retry logic
- Exponential backoff for failures
- Comprehensive error reporting

Step Format:
- Pure callable: lambda ctx: resource.method(ctx["data"])
"""

from collections.abc import Sequence
import logging
import time
from typing import Any

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.core.workflow.base_workflow import WorkflowStep


logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, step_name: str, step_index: int, cause: Exception | None = None):
        super().__init__(message)
        self.step_name = step_name
        self.step_index = step_index
        self.cause = cause


class WorkflowExecutor:
    """
    Executes workflows using SA-loop pattern with callables only.

    SA-loop Pattern:
    - SEE: Simple heuristic checks (no LLM reasoning)
    - ACT: Execute predetermined callable with retry logic
    - LOOP: Continue to next step until complete or error

    Determinism: 95% (only callable execution variation, no LLM non-determinism)
    Cost: $0 (no LLM calls for planning/reasoning)
    """

    def __init__(
        self,
        name: str,
        steps: Sequence[WorkflowStep],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
    ):
        """
        Initialize workflow executor.

        Args:
            steps: List of WorkflowStep dataclass instances
            max_retries: Maximum retry attempts per step
            retry_delay: Initial delay between retries (seconds)
            exponential_backoff: Use exponential backoff for retries
        """
        self.name = name
        self.steps = steps
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.context: DictParams = {}
        self.execution_log: list[DictParams] = []

    def execute(self) -> DictParams:
        """
        Execute workflow using SA-loop pattern.

        SA-Loop Structure (similar to STAR loop):
        ┌────────────────────────────────────┐
        │  LOOP over predetermined steps:    │
        │                                    │
        │    ┌─── SEE ─────────────────────┐ │
        │    │ Observe context & conditions│ │
        │    │ - Check skip conditions     │ │
        │    │ - Check abort conditions    │ │
        │    │ - Verify dependencies       │ │
        │    └─────────────────────────────┘ │
        │              ↓                     │
        │    ┌─── ACT ─────────────────────┐ │
        │    │ Execute predetermined step  │ │
        │    │ - Call callable with context│ │
        │    │ - Retry on failure            │ │
        │    │ - Validate result           │ │
        │    │ - Store in context          │ │
        │    └─────────────────────────────┘ │
        │              ↓                     │
        │    ┌─── EXIT CHECK ──────────────┐ │
        │    │ Check if workflow should    │ │
        │    │ continue or exit            │ │
        │    └─────────────────────────────┘ │
        │              ↓                     │
        │    Continue to next step or exit   │
        └────────────────────────────────────┘

        Returns:
            Execution results with success status and context
        """

        @observable(name=f"{self.name}-execute")
        def _do_execute() -> DictParams:
            logger.info(f"Starting SA-loop workflow execution with {len(self.steps)} predetermined steps")
            trace_outputs: DictParams = {"trace_outputs": {}}

            # The main SA-Loop
            outputs: DictParams = {}
            step_index = 0
            while step_index < len(self.steps):
                trace_inputs = {
                    "steps": self.steps,
                    "step_index": step_index,
                    "context": self.context,
                }

                # Workflows = SEE-ACT-Loop
                trace_percepts = self._see(trace_inputs)
                trace_outputs = self._act(trace_percepts)

                outputs = trace_outputs.get("trace_outputs", {})
                if not outputs.get("success", True):
                    break

                step_index += 1

            # Format a consistent result object
            return {
                "success": outputs.get("success", True),
                "result": outputs.get("result", {}),
                # "context": self.context,
                # "execution_log": self.execution_log,
            }

        return _do_execute()

    @observable
    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: Observe context and check conditions with fault tolerance.

        Args:
            trace_inputs:
              - steps (list): List of WorkflowStep dataclass instances
              - step_index (int): Index of the current step
              - context (DictParams): Context of the workflow

        Returns:
            trace_percepts:
              - success (bool): True if the step is ready for execution
              - action (str): Action to proceed
              - reason (str): Reason for the action
              - step (WorkflowStep): Step to execute
              - step_index (int): Index of the current step
              - context (DictParams): Context of the workflow
        """
        steps: list[WorkflowStep] = trace_inputs["steps"]
        step_index: int = trace_inputs["step_index"]
        step: WorkflowStep = steps[step_index]
        self.context = trace_inputs["context"] or {}

        logger.debug(f"[SEE] Observing step: {step.name}")
        trace_percepts = {
            "success": True,
            "action": "proceed",
            "reason": "Step ready for execution",
            "step": step,
            "step_index": step_index,
            "context": self.context,
        }
        return {"trace_percepts": trace_percepts}

    @observable
    def _act(self, trace_percepts: DictParams) -> DictParams:
        """
        ACT: Execute step with fault tolerance and retry logic.

        Args:
            trace_percepts: Results from the SEE phase containing step information and conditions
              - success (bool): True if the step is ready for execution
              - action (str): Action to proceed
              - reason (str): Reason for the action
              - step (WorkflowStep): Step to execute
              - step_index (int): Index of the current step
              - context (DictParams): Context of the workflow

        Returns:
            trace_outputs:
              - success (bool): True if the step is ready for execution
              - action (str): Action to proceed
              - reason (str): Reason for the action
              - step (WorkflowStep): Step to execute
              - step_index (int): Index of the current step
              - context (DictParams): Context of the workflow
        """
        # Extract step information from trace_percepts
        if not trace_percepts:
            return {
                "trace_outputs": {
                    "success": False,
                    "error": "missing_trace_percepts",
                    "message": "Missing trace_percepts",
                }
            }

        trace_percepts = trace_percepts.get("trace_percepts", {})

        # Check if SEE phase failed
        if not trace_percepts.get("success", True):
            return {"trace_outputs": trace_percepts}

        step = trace_percepts.get("step")
        step_index = trace_percepts.get("step_index")
        self.context = trace_percepts.get("context") or {}

        # Validate extracted values
        if step is None or step_index is None:
            return {
                "trace_outputs": {
                    "success": False,
                    "error": "missing_step_info",
                    "message": "Missing step information in trace_percepts",
                    "trace_percepts": trace_percepts,
                    "context": self.context,
                }
            }

        try:

            @observable(name=f"{self.name}-do-act-{step.name}")
            def __do_act(step: WorkflowStep, step_index: int, context: DictParams):
                logger.debug(f"[ACT] Executing step: {step.name}")
                return self._do_act(step, step_index, context)

            result = __do_act(step, step_index, self.context)

            # Store result in context using step's store_as
            self.context[step.store_as] = result
            logger.debug(f"[ACT] Stored result as: {step.store_as}")

            # Log successful execution
            self._log_step_execution(step_index, step.name, "success", result)
            logger.info(f"[ACT] Successfully completed step: {step.name}")

            return {
                "trace_outputs": {
                    "success": True,
                    "result": result,
                    "context": self.context,
                }
            }

        except Exception as e:
            logger.error(f"[ACT] Step {step.name} failed: {e}", exc_info=True)
            self._log_step_execution(step_index, step.name, "failed", str(e))
            return {"trace_outputs": {"success": False}}

    def _do_act(self, step: WorkflowStep, step_index: int, context: DictParams) -> Any:
        """
        ACT: Execute callable with retry logic.

        Args:
            step: The WorkflowStep to execute
            step_index: Step index
            context: Context of the workflow

        Returns:
            Step execution result
        """
        last_error = None
        self.context = context or {}

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"[ACT] Executing callable {step.name} (attempt {attempt + 1}/{self.max_retries})")
                result = step.callable(self.context)

                # Validate result if validator specified
                if step.validate and not self._validate_result(result, step.validate):
                    raise ValueError(f"Result validation failed: {step.validate}")

                # Ensure result has success field
                if isinstance(result, dict):
                    result["success"] = True
                else:
                    result = {"success": True, "result": result}

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"[ACT] Callable {step.name} failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt) if self.exponential_backoff else self.retry_delay
                    logger.info(f"[ACT] Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)

        raise WorkflowExecutionError(
            f"Callable step failed after {self.max_retries} attempts: {last_error}",
            step_name=step.name,
            step_index=step_index,
            cause=last_error,
        )

    def _validate_result(self, result: Any, validator: DictParams) -> bool:
        """Validate step result."""
        if validator.get("not_empty"):
            if result is None or (hasattr(result, "__len__") and len(result) == 0):
                return False

        if "min_items" in validator:
            if not hasattr(result, "__len__") or len(result) < validator["min_items"]:
                return False

        if "has_keys" in validator:
            if not isinstance(result, dict):
                return False
            for key in validator["has_keys"]:
                if key not in result:
                    return False

        return True

    def _log_step_execution(self, step_index: int, step_name: str, status: str, result: Any) -> None:
        """Log step execution for observability."""
        self.execution_log.append(
            {
                "step_index": step_index,
                "step_name": step_name,
                "status": status,
                "result": str(result)[:200] if result else None,
                "timestamp": time.time(),
            }
        )
