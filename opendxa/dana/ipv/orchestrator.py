"""
IPV Orchestrator - Coordinates the execution of IPV phases.

This module provides the IPVOrchestrator class that manages the execution
of the three IPV phases (Infer-Process-Validate) in sequence, handling
errors, retries, and configuration.
"""

import time
from typing import Any, Dict, List, Optional

from .base import IPVConfig, IPVError, IPVExecutionError, IPVPhase, IPVResult
from .phases import InferPhase, ProcessPhase, ValidatePhase


class IPVOrchestrator:
    """
    Orchestrates the execution of IPV phases.

    The orchestrator manages the flow through the three phases:
    1. INFER: Liberal input acceptance and context collection
    2. PROCESS: Generous transformation and execution
    3. VALIDATE: Conservative output guarantee
    """

    def __init__(
        self, infer_phase: Optional[IPVPhase] = None, process_phase: Optional[IPVPhase] = None, validate_phase: Optional[IPVPhase] = None
    ):
        """
        Initialize the orchestrator with IPV phases.

        Args:
            infer_phase: Custom INFER phase (uses default if None)
            process_phase: Custom PROCESS phase (uses default if None)
            validate_phase: Custom VALIDATE phase (uses default if None)
        """
        self.infer_phase = infer_phase or InferPhase()
        self.process_phase = process_phase or ProcessPhase()
        self.validate_phase = validate_phase or ValidatePhase()

        self._debug_mode = False
        self._execution_history: List[Dict[str, Any]] = []

    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug mode for all phases."""
        self._debug_mode = enabled
        self.infer_phase.set_debug_mode(enabled)
        self.process_phase.set_debug_mode(enabled)
        self.validate_phase.set_debug_mode(enabled)

    def execute_ipv_pipeline(self, input_data: Any, context: Any = None, config: Optional[IPVConfig] = None) -> IPVResult:
        """
        Execute the complete IPV pipeline.

        Args:
            input_data: The original input to process
            context: Execution context (e.g., SandboxContext)
            config: IPV configuration (uses defaults if None)

        Returns:
            IPVResult with the final validated output
        """
        if config is None:
            config = IPVConfig()

        if config.debug_mode:
            self.set_debug_mode(True)

        start_time = time.time()
        execution_id = f"ipv_{int(start_time * 1000)}"

        self._log_debug(f"Starting IPV pipeline execution {execution_id}")

        # Track execution for debugging and learning
        execution_record = {
            "execution_id": execution_id,
            "start_time": start_time,
            "input_data": input_data,
            "config": config.to_dict(),
            "phases": {},
            "iterations": 0,
            "success": False,
            "final_result": None,
            "total_time": 0,
            "errors": [],
        }

        try:
            # Execute with potential iterations
            final_result = self._execute_with_iterations(input_data, context, config, execution_record)

            execution_record["success"] = True
            execution_record["final_result"] = final_result.result
            execution_record["total_time"] = time.time() - start_time

            self._execution_history.append(execution_record)

            self._log_debug(f"IPV pipeline {execution_id} completed successfully in {execution_record['total_time']:.3f}s")

            return final_result

        except Exception as e:
            execution_record["success"] = False
            execution_record["total_time"] = time.time() - start_time
            execution_record["errors"].append(str(e))

            self._execution_history.append(execution_record)

            self._log_debug(f"IPV pipeline {execution_id} failed: {e}")

            return IPVResult(
                success=False,
                result=None,
                error=IPVExecutionError(f"IPV pipeline failed: {e}", original_error=e),
                execution_time=execution_record["total_time"],
                metadata={"execution_id": execution_id, "execution_record": execution_record},
            )

    def _execute_with_iterations(self, input_data: Any, context: Any, config: IPVConfig, execution_record: Dict[str, Any]) -> IPVResult:
        """Execute IPV pipeline with iteration support."""

        max_iterations = config.max_iterations
        last_error = None

        for iteration in range(max_iterations):
            execution_record["iterations"] = iteration + 1

            self._log_debug(f"Starting iteration {iteration + 1}/{max_iterations}")

            try:
                # Execute single iteration
                result = self._execute_single_iteration(input_data, context, config, iteration, execution_record)

                if result.is_success():
                    self._log_debug(f"Iteration {iteration + 1} succeeded")
                    return result
                else:
                    last_error = result.error
                    self._log_debug(f"Iteration {iteration + 1} failed: {last_error}")

                    # For now, don't retry - just fail
                    # In a full implementation, we would analyze the error
                    # and potentially modify the approach for the next iteration
                    break

            except Exception as e:
                last_error = e
                self._log_debug(f"Iteration {iteration + 1} threw exception: {e}")

                # For now, don't retry on exceptions
                break

        # All iterations failed
        raise IPVExecutionError(f"IPV pipeline failed after {execution_record['iterations']} iterations", original_error=last_error)

    def _execute_single_iteration(
        self, input_data: Any, context: Any, config: IPVConfig, iteration: int, execution_record: Dict[str, Any]
    ) -> IPVResult:
        """Execute a single iteration of the IPV pipeline."""

        iteration_record = {"iteration": iteration, "phases": {}, "success": False, "error": None}

        try:
            # Phase 1: INFER
            self._log_debug("Executing INFER phase")
            infer_result = self.infer_phase.execute(input_data, context, config)
            iteration_record["phases"]["infer"] = {
                "success": infer_result.is_success(),
                "execution_time": infer_result.execution_time,
                "error": str(infer_result.error) if infer_result.error else None,
            }

            if not infer_result.is_success():
                raise infer_result.error or IPVExecutionError("INFER phase failed")

            # Phase 2: PROCESS
            self._log_debug("Executing PROCESS phase")
            process_result = self.process_phase.execute(infer_result.result, context, config)
            iteration_record["phases"]["process"] = {
                "success": process_result.is_success(),
                "execution_time": process_result.execution_time,
                "error": str(process_result.error) if process_result.error else None,
            }

            if not process_result.is_success():
                raise process_result.error or IPVExecutionError("PROCESS phase failed")

            # Phase 3: VALIDATE
            self._log_debug("Executing VALIDATE phase")
            validate_result = self.validate_phase.execute(process_result.result, infer_result.result, config)
            iteration_record["phases"]["validate"] = {
                "success": validate_result.is_success(),
                "execution_time": validate_result.execution_time,
                "error": str(validate_result.error) if validate_result.error else None,
            }

            if not validate_result.is_success():
                raise validate_result.error or IPVExecutionError("VALIDATE phase failed")

            # All phases succeeded
            iteration_record["success"] = True

            # Store iteration record
            if "iterations_detail" not in execution_record:
                execution_record["iterations_detail"] = []
            execution_record["iterations_detail"].append(iteration_record)

            # Return final result
            total_time = sum([infer_result.execution_time or 0, process_result.execution_time or 0, validate_result.execution_time or 0])

            return IPVResult(
                success=True,
                result=validate_result.result,
                execution_time=total_time,
                metadata={
                    "iteration": iteration,
                    "infer_metadata": infer_result.metadata,
                    "process_metadata": process_result.metadata,
                    "validate_metadata": validate_result.metadata,
                    "phase_times": {
                        "infer": infer_result.execution_time,
                        "process": process_result.execution_time,
                        "validate": validate_result.execution_time,
                    },
                },
            )

        except Exception as e:
            iteration_record["success"] = False
            iteration_record["error"] = str(e)

            # Store failed iteration record
            if "iterations_detail" not in execution_record:
                execution_record["iterations_detail"] = []
            execution_record["iterations_detail"].append(iteration_record)

            return IPVResult(
                success=False,
                result=None,
                error=e if isinstance(e, IPVError) else IPVExecutionError(str(e), original_error=e),
                metadata={"iteration": iteration, "iteration_record": iteration_record},
            )

    def _log_debug(self, message: str, **kwargs) -> None:
        """Log debug information if debug mode is enabled."""
        if self._debug_mode:
            print(f"[IPV-ORCHESTRATOR] {message}", **kwargs)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the history of IPV pipeline executions."""
        return self._execution_history.copy()

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from execution history."""
        if not self._execution_history:
            return {"total_executions": 0}

        successful = [e for e in self._execution_history if e["success"]]
        failed = [e for e in self._execution_history if not e["success"]]

        stats = {
            "total_executions": len(self._execution_history),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate": len(successful) / len(self._execution_history) if self._execution_history else 0,
        }

        if successful:
            times = [e["total_time"] for e in successful]
            stats.update(
                {
                    "avg_execution_time": sum(times) / len(times),
                    "min_execution_time": min(times),
                    "max_execution_time": max(times),
                }
            )

        if failed:
            common_errors = {}
            for execution in failed:
                for error in execution.get("errors", []):
                    common_errors[error] = common_errors.get(error, 0) + 1
            stats["common_errors"] = common_errors

        return stats
