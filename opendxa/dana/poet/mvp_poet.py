"""
POET MVP Implementation - POE-Focused Framework for Immediate Value

This module provides the POEExecutor class and poet decorator for enhancing
functions with the core POE (Perceive → Operate → Enforce) pipeline.
The T-stage (Train) is optional and can be enabled separately.
"""

import json
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from .errors import (
    POEError,
    PerceiveError,
    OperateError,
    EnforceError,
    TrainError,
    DomainPluginError,
    RetryExhaustedError,
    TimeoutError,
    ConfigurationError,
    create_context,
    wrap_poe_error,
)
from .metrics import POEMetricsCollector, get_global_collector


class POEConfig:
    """POE-focused configuration for simplified POET implementation."""

    def __init__(
        self,
        retries: int = 3,
        timeout: float = 30.0,
        domain: Optional[str] = None,
        enable_training: bool = False,
        collect_metrics: bool = True,
    ):
        """
        Initialize POE configuration.

        Args:
            retries: Number of retry attempts on failure
            timeout: Timeout in seconds for function execution
            domain: Domain-specific plugin to load (optional)
            enable_training: Enable optional T-stage learning (default: False)
            collect_metrics: Enable metrics collection (default: True)
        """
        self.retries = retries
        self.timeout = timeout
        self.domain = domain
        self.enable_training = enable_training
        self.collect_metrics = collect_metrics


class POEMetrics:
    """Simple metrics collection for POE pipeline monitoring."""

    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.avg_execution_time = 0.0
        self.retry_count = 0

    def record_execution(self, success: bool, execution_time: float, attempts: int):
        """Record execution metrics."""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update average execution time
        self.avg_execution_time = (self.avg_execution_time * (self.total_executions - 1) + execution_time) / self.total_executions

        if attempts > 1:
            self.retry_count += attempts - 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        return {
            "total_executions": self.total_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "failure_rate": self.failed_executions / max(self.total_executions, 1),
            "avg_execution_time": self.avg_execution_time,
            "total_retries": self.retry_count,
        }


class POEExecutor(Loggable):
    """
    POE-focused executor implementing Perceive → Operate → Enforce pipeline.

    This simplified implementation provides the core value of POET while keeping
    the architecture clean and maintainable. The T-stage is optional and can be
    enabled when needed.
    """

    def __init__(self, config: POEConfig):
        super().__init__()
        self.config = config
        self.domain_plugin = self._load_domain_plugin()
        self.function_name = None  # Set when wrapping a function
        self.metrics = POEMetrics() if config.collect_metrics else None

        # Optional T-stage components (loaded only if training enabled)
        self.parameters = None
        if config.enable_training:
            self.function_name = None  # Will be set later

    def __call__(self, func: Callable) -> Callable:
        """Wrap a function with POE enhancement."""
        self.function_name = func.__name__

        # Initialize T-stage components if training is enabled
        if self.config.enable_training:
            self.parameters = self._load_parameters()

        @wraps(func)
        def poe_wrapper(*args, **kwargs):
            start_time = time.time()
            execution_result = None
            stage_timings = {}

            try:
                # P: Perceive - Input optimization and preprocessing
                perceive_start = time.time()
                perceived_input = self._perceive(args, kwargs)
                stage_timings["perceive"] = time.time() - perceive_start

                # O: Operate - Execute with reliability and retry logic
                operate_start = time.time()
                operation_result = self._operate_with_retry(func, perceived_input)
                stage_timings["operate"] = time.time() - operate_start

                # E: Enforce - Output validation and quality assurance
                enforce_start = time.time()
                enforced_result = self._enforce(operation_result, perceived_input)
                stage_timings["enforce"] = time.time() - enforce_start

                execution_result = {
                    "success": True,
                    "result": enforced_result,
                    "execution_time": time.time() - start_time,
                    "attempts": operation_result.get("attempt", 1),
                }

                # Optional T: Train - Learning and parameter optimization
                if self.config.enable_training:
                    train_start = time.time()
                    try:
                        self._train(perceived_input, execution_result)
                        stage_timings["train"] = time.time() - train_start
                    except Exception as learning_error:
                        stage_timings["train"] = time.time() - train_start
                        self.warning(f"T-stage learning failed but continuing execution: {learning_error}")

                # Record metrics if enabled
                if self.metrics:
                    self.metrics.record_execution(True, execution_result["execution_time"], execution_result["attempts"])

                    # Also record detailed metrics if global collector is available
                    try:
                        global_collector = get_global_collector()
                        global_collector.record_execution(
                            function_name=func.__name__,
                            success=True,
                            total_time=execution_result["execution_time"],
                            attempts=execution_result["attempts"],
                            domain=self.config.domain,
                            stage_timings=stage_timings,
                            config_info={
                                "retries": self.config.retries,
                                "timeout": self.config.timeout,
                                "training_enabled": self.config.enable_training,
                            },
                        )
                    except Exception as metrics_error:
                        self.debug(f"Detailed metrics collection failed: {metrics_error}")

                return enforced_result

            except Exception as e:
                execution_time = time.time() - start_time
                self.error(f"POE execution failed for {func.__name__}: {e}")

                # Record failure metrics
                if self.metrics:
                    attempts = operation_result.get("attempt", 1) if execution_result else 1
                    self.metrics.record_execution(False, execution_time, attempts)

                    # Also record detailed metrics if global collector is available
                    try:
                        global_collector = get_global_collector()
                        global_collector.record_execution(
                            function_name=func.__name__,
                            success=False,
                            total_time=execution_time,
                            attempts=attempts,
                            domain=self.config.domain,
                            stage_timings=stage_timings,
                            error_info={
                                "type": type(e).__name__,
                                "message": str(e),
                                "stage": getattr(e, "stage", "unknown") if isinstance(e, POEError) else "unknown",
                            },
                            config_info={
                                "retries": self.config.retries,
                                "timeout": self.config.timeout,
                                "training_enabled": self.config.enable_training,
                            },
                        )
                    except Exception as metrics_error:
                        self.debug(f"Detailed metrics collection failed: {metrics_error}")

                # Wrap in POE-specific error if not already
                if not isinstance(e, POEError):
                    context = create_context(function_name=func.__name__, domain=self.config.domain, execution_time=execution_time)
                    raise wrap_poe_error(func.__name__, "operate", e, context)
                else:
                    raise

        return poe_wrapper

    def _perceive(self, args, kwargs) -> Dict[str, Any]:
        """
        P: Perceive - Input processing with domain intelligence.

        This stage analyzes and optimizes inputs before execution.
        """
        try:
            if self.domain_plugin:
                self.debug("Applying domain-specific input processing")
                return self.domain_plugin.process_inputs(args, kwargs)

            # Default input structure
            return {"args": args, "kwargs": kwargs}

        except Exception as e:
            self.warning(f"Perceive stage failed, using original inputs: {e}")
            return {"args": args, "kwargs": kwargs}

    def _operate_with_retry(self, func: Callable, perceived_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        O: Operate - Execute function with reliability patterns.

        This stage handles the core function execution with retry logic,
        timeout handling, and error recovery.
        """
        last_exception = None

        for attempt in range(self.config.retries + 1):
            try:
                start_time = time.time()

                self.debug(f"Executing function (attempt {attempt + 1}/{self.config.retries + 1})")

                # Execute the function
                result = func(*perceived_input["args"], **perceived_input["kwargs"])

                execution_time = time.time() - start_time

                # Check timeout (warning only, don't fail)
                if execution_time > self.config.timeout:
                    self.warning(f"Function execution took {execution_time:.2f}s (timeout: {self.config.timeout}s)")

                return {"result": result, "execution_time": execution_time, "attempt": attempt + 1, "success": True}

            except Exception as e:
                last_exception = e
                self.debug(f"Attempt {attempt + 1} failed: {e}")

                if attempt < self.config.retries:
                    # Exponential backoff with cap
                    wait_time = min(2**attempt, 8)
                    self.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # All retries exhausted
        self.error(f"All {self.config.retries + 1} attempts failed")
        raise last_exception

    def _enforce(self, operation_result: Dict[str, Any], perceived_input: Dict[str, Any]) -> Any:
        """
        E: Enforce - Output validation and quality assurance.

        This stage validates the operation result and applies domain-specific
        quality checks before returning the final result.
        """
        try:
            if self.domain_plugin:
                self.debug("Applying domain-specific output validation")
                return self.domain_plugin.validate_output(operation_result, perceived_input)

            # Basic validation - ensure we have a successful result
            if operation_result.get("success", False):
                return operation_result["result"]
            else:
                raise ValueError("Operation did not complete successfully")

        except Exception as e:
            self.warning(f"Enforce stage failed: {e}")
            # Return raw result if validation fails
            return operation_result.get("result") if isinstance(operation_result, dict) else operation_result

    def _train(self, perceived_input: Dict[str, Any], execution_result: Dict[str, Any]):
        """
        T: Train - Optional learning and parameter optimization.

        This stage is only active when enable_training=True. It learns from
        execution patterns and adjusts parameters for better performance.
        """
        if not self.config.enable_training or not self.parameters:
            return

        try:
            success = execution_result.get("success", False)
            execution_time = execution_result.get("execution_time", 0)

            # Simple learning rules for parameter adjustment
            if not success and self.parameters.get("retries", 3) < 5:
                self.parameters["retries"] += 1
                self.debug("T-stage: Increased retry count due to failure")

            elif success and execution_time > self.config.timeout * 0.8:
                # Increase timeout if we're consistently near the limit
                new_timeout = min(self.config.timeout * 1.2, 120)
                self.parameters["timeout"] = new_timeout
                self.debug(f"T-stage: Increased timeout to {new_timeout}s due to slow execution")

            elif success and execution_time < self.config.timeout * 0.3:
                # Decrease timeout if consistently fast
                new_timeout = max(self.config.timeout * 0.9, 5)
                self.parameters["timeout"] = new_timeout
                self.debug(f"T-stage: Decreased timeout to {new_timeout}s due to fast execution")

            # Save updated parameters
            self._save_parameters()

        except Exception as e:
            self.warning(f"T-stage learning failed: {e}")

    def _load_domain_plugin(self):
        """Load domain-specific plugin if specified."""
        if not self.config.domain:
            return None

        try:
            from .domains import PLUGIN_REGISTRY

            plugin_class = PLUGIN_REGISTRY.get_plugin(self.config.domain)
            if plugin_class:
                self.debug(f"Loaded domain plugin: {self.config.domain}")
                return plugin_class()
            else:
                available_domains = PLUGIN_REGISTRY.list_domains()
                self.warning(f"Unknown domain: {self.config.domain}. Available domains: {available_domains}")
                return None

        except ImportError as e:
            self.warning(f"Could not load domain plugin for {self.config.domain}: {e}")
            return None

    def _load_parameters(self):
        """Load parameters from JSON storage (T-stage only)."""
        if not self.config.enable_training:
            return None

        try:
            params_file = self._get_parameters_file()
            if params_file.exists():
                with open(params_file, "r") as f:
                    return json.load(f)
            else:
                # Default parameters
                return {"retries": self.config.retries, "timeout": self.config.timeout}
        except Exception as e:
            self.warning(f"Could not load T-stage parameters: {e}")
            return {"retries": self.config.retries, "timeout": self.config.timeout}

    def _save_parameters(self):
        """Save parameters to JSON storage (T-stage only)."""
        if not self.config.enable_training or not self.parameters:
            return

        try:
            params_file = self._get_parameters_file()
            params_file.parent.mkdir(parents=True, exist_ok=True)

            with open(params_file, "w") as f:
                json.dump(self.parameters, f, indent=2)

        except Exception as e:
            self.warning(f"Could not save T-stage parameters: {e}")

    def _get_parameters_file(self):
        """Get the path to the parameters file."""
        # Store in user's home directory under .opendxa/poet/
        home_dir = Path.home()
        poet_dir = home_dir / ".opendxa" / "poet"

        # Use function name and domain for unique parameter sets
        if self.function_name:
            filename = f"{self.function_name}"
            if self.config.domain:
                filename += f"_{self.config.domain}"
            filename += "_params.json"
        else:
            filename = "default_params.json"

        return poet_dir / filename

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current POE execution metrics."""
        if self.metrics:
            return self.metrics.get_stats()
        return None


def poet(
    retries: int = 3, timeout: float = 30.0, domain: Optional[str] = None, enable_training: bool = False, collect_metrics: bool = True
) -> Callable:
    """
    POE-focused POET decorator for enhanced function execution.

    This decorator implements the core POE (Perceive → Operate → Enforce) pipeline
    with optional T-stage (Train) functionality. It provides immediate value through
    reliability improvements while keeping the architecture simple and maintainable.

    Args:
        retries: Number of retry attempts on failure (default: 3)
        timeout: Timeout in seconds for function execution (default: 30.0)
        domain: Domain-specific plugin to load (optional)
        enable_training: Enable optional T-stage learning (default: False)
        collect_metrics: Enable metrics collection (default: True)

    Returns:
        Decorated function with POE enhancements

    Examples:
        Basic POE enhancement:
        ```python
        @poet()
        def my_function():
            # Reliability + performance optimization
            return "result"
        ```

        With domain expertise:
        ```python
        @poet(domain="building_management")
        def control_hvac():
            # + Domain-specific intelligence
            return hvac_status
        ```

        With T-stage learning:
        ```python
        @poet(domain="llm_optimization", enable_training=True)
        def enhanced_reasoning():
            # + Adaptive parameter learning
            return reasoning_result
        ```
    """
    config = POEConfig(retries, timeout, domain, enable_training, collect_metrics)
    executor = POEExecutor(config)
    return executor


# Legacy compatibility aliases
SimplePOETConfig = POEConfig
SimplePOETExecutor = POEExecutor
