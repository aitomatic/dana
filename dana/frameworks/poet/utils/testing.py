"""
Testing and debugging utilities for POET development.

This module provides tools to test POET-enhanced functions in isolation,
debug phase execution, and validate POET behavior.
"""

import time
from collections.abc import Callable
from typing import Any

from dana.frameworks.poet.core.types import POETConfig, POETResult


class POETTestMode:
    """Context manager for testing POET functions with mocked phases."""

    def __init__(self, mock_phases: list[str] | None = None, debug: bool = False):
        self.mock_phases = mock_phases or []
        self.debug = debug
        self.original_phases = {}

    def __enter__(self):
        if self.debug:
            print(f"🧪 Entering POET test mode with mocked phases: {self.mock_phases}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.debug:
            print("🧪 Exiting POET test mode")


class POETPhaseDebugger:
    """Debugger for stepping through POET phases individually."""

    def __init__(self, function: Callable, config: POETConfig):
        self.function = function
        self.config = config
        self.phase_results = {}

    def debug_perceive(self, *args, **kwargs) -> dict[str, Any]:
        """Debug the perceive phase in isolation."""
        print(f"🔍 Debugging PERCEIVE phase for {self.function.__name__}")

        start_time = time.time()

        # Simulate perceive phase logic
        context = {
            "function_name": self.function.__name__,
            "args": args,
            "kwargs": kwargs,
            "domain": self.config.domain,
            "phase": "perceive",
        }

        # Apply perceive configuration
        if self.config.perceive.get("input_validation", False):
            print("  ✓ Input validation enabled")

        if self.config.perceive.get("normalize_formats", False):
            print("  ✓ Format normalization enabled")

        execution_time = time.time() - start_time
        result = {"context": context, "execution_time": execution_time, "phase": "perceive"}

        self.phase_results["perceive"] = result
        print(f"  ⏱️  Perceive phase completed in {execution_time:.3f}s")
        return result

    def debug_operate(self, *args, **kwargs) -> dict[str, Any]:
        """Debug the operate phase in isolation."""
        print(f"⚙️  Debugging OPERATE phase for {self.function.__name__}")

        start_time = time.time()

        # Execute the actual function
        try:
            result = self.function(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        execution_time = time.time() - start_time

        phase_result = {
            "result": result,
            "success": success,
            "error": error,
            "execution_time": execution_time,
            "retries_configured": self.config.retries,
            "timeout_configured": self.config.timeout,
            "phase": "operate",
        }

        self.phase_results["operate"] = phase_result
        print(f"  ⏱️  Operate phase completed in {execution_time:.3f}s")
        print(f"  ✓ Success: {success}")
        if error:
            print(f"  ❌ Error: {error}")

        return phase_result

    def debug_enforce(self, operation_result: Any) -> dict[str, Any]:
        """Debug the enforce phase in isolation."""
        print(f"🛡️  Debugging ENFORCE phase for {self.function.__name__}")

        start_time = time.time()

        # Apply enforce configuration
        validated_result = operation_result
        validations_applied = []

        if self.config.enforce.get("output_validation", False):
            validations_applied.append("output_validation")
            print("  ✓ Output validation enabled")

        if self.config.enforce.get("compliance_check"):
            compliance_type = self.config.enforce["compliance_check"]
            validations_applied.append(f"compliance_check_{compliance_type}")
            print(f"  ✓ Compliance check ({compliance_type}) enabled")

        execution_time = time.time() - start_time

        phase_result = {
            "validated_result": validated_result,
            "validations_applied": validations_applied,
            "execution_time": execution_time,
            "phase": "enforce",
        }

        self.phase_results["enforce"] = phase_result
        print(f"  ⏱️  Enforce phase completed in {execution_time:.3f}s")
        return phase_result

    def debug_train(self, operation_result: Any) -> dict[str, Any]:
        """Debug the train phase in isolation."""
        print(f"🎓 Debugging TRAIN phase for {self.function.__name__}")

        start_time = time.time()

        # Apply train configuration
        training_actions = []

        if self.config.train.get("learning_rate"):
            learning_rate = self.config.train["learning_rate"]
            training_actions.append(f"learning_rate_{learning_rate}")
            print(f"  ✓ Learning rate: {learning_rate}")

        if self.config.train.get("feedback_threshold"):
            threshold = self.config.train["feedback_threshold"]
            training_actions.append(f"feedback_threshold_{threshold}")
            print(f"  ✓ Feedback threshold: {threshold}")

        execution_time = time.time() - start_time

        phase_result = {"training_actions": training_actions, "execution_time": execution_time, "phase": "train"}

        self.phase_results["train"] = phase_result
        print(f"  ⏱️  Train phase completed in {execution_time:.3f}s")
        return phase_result

    def debug_full_execution(self, *args, **kwargs) -> dict[str, Any]:
        """Debug all phases in sequence."""
        print(f"🔍 Full POET execution debug for {self.function.__name__}")
        print("=" * 50)

        total_start = time.time()

        # Execute all phases
        perceive_result = self.debug_perceive(*args, **kwargs)
        operate_result = self.debug_operate(*args, **kwargs)
        enforce_result = self.debug_enforce(operate_result["result"])

        if self.config.train:
            train_result = self.debug_train(operate_result["result"])
        else:
            train_result = {"phase": "train", "skipped": True}

        total_time = time.time() - total_start

        summary = {
            "total_execution_time": total_time,
            "phases": {"perceive": perceive_result, "operate": operate_result, "enforce": enforce_result, "train": train_result},
            "final_result": enforce_result["validated_result"],
        }

        print("=" * 50)
        print(f"🎯 Total execution time: {total_time:.3f}s")
        print(f"🎯 Final result: {summary['final_result']}")

        return summary


def debug_poet_function(func: Callable, config: POETConfig, *args, **kwargs) -> dict[str, Any]:
    """
    Debug a POET function execution step by step.

    Args:
        func: The function to debug
        config: POET configuration
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Debug summary with phase-by-phase execution details
    """
    debugger = POETPhaseDebugger(func, config)
    return debugger.debug_full_execution(*args, **kwargs)


def test_poet_function(func: Callable, test_cases: list[dict[str, Any]], config: POETConfig | None = None) -> dict[str, Any]:
    """
    Test a POET function with multiple test cases.

    Args:
        func: The function to test
        test_cases: List of test cases with 'args', 'kwargs', and 'expected' keys
        config: Optional POET configuration for debugging

    Returns:
        Test results summary
    """
    results = {"function_name": func.__name__, "total_tests": len(test_cases), "passed": 0, "failed": 0, "errors": [], "test_details": []}

    for i, test_case in enumerate(test_cases):
        args = test_case.get("args", [])
        kwargs = test_case.get("kwargs", {})
        expected = test_case.get("expected")

        try:
            result = func(*args, **kwargs)

            # Handle POETResult objects
            if isinstance(result, POETResult):
                actual_result = result._result
                poet_metadata = result._poet
            else:
                actual_result = result
                poet_metadata = None

            passed = actual_result == expected

            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"test_case": i, "expected": expected, "actual": actual_result, "args": args, "kwargs": kwargs})

            results["test_details"].append(
                {"test_case": i, "passed": passed, "result": actual_result, "expected": expected, "poet_metadata": poet_metadata}
            )

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"test_case": i, "error": str(e), "args": args, "kwargs": kwargs})

    return results


def performance_benchmark(func: Callable, iterations: int = 100, *args, **kwargs) -> dict[str, Any]:
    """
    Benchmark the performance of a POET function.

    Args:
        func: The function to benchmark
        iterations: Number of iterations to run
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Performance statistics
    """
    execution_times = []

    for _ in range(iterations):
        start_time = time.time()
        try:
            func(*args, **kwargs)
        except Exception:
            pass  # Ignore errors in benchmark

        execution_time = time.time() - start_time
        execution_times.append(execution_time)

    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    return {
        "function_name": func.__name__,
        "iterations": iterations,
        "average_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "total_time": sum(execution_times),
        "success_rate": sum(1 for t in execution_times if t > 0) / iterations,
    }
