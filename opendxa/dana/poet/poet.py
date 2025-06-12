"""
POET Unified Implementation - POE-Focused Framework with Advanced Learning

This module provides the POEExecutor class and poet decorator for enhancing
functions with the core POET (Perceive → Operate → Enforce) pipeline.
The T-stage (Train) supports both basic and advanced learning algorithms.
"""

import json
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from opendxa.common.mixins.loggable import Loggable

from .errors import (
    POETError,
    create_context,
    wrap_poe_error,
)
from .metrics import get_global_collector


class POETConfig:
    """POE-focused configuration for unified POET implementation."""

    def __init__(
        self,
        retries: int = 3,
        timeout: float = 30.0,
        domain: str | None = None,
        enable_training: bool = False,
        collect_metrics: bool = True,
        # Advanced learning parameters (optional)
        learning_algorithm: str = "basic",
        learning_rate: float = 0.05,
        convergence_threshold: float = 0.01,
        enable_cross_function_learning: bool = False,
        performance_tracking: bool = True,
    ):
        """
        Initialize POET configuration.

        Args:
            retries: Number of retry attempts on failure
            timeout: Timeout in seconds for function execution
            domain: Domain-specific plugin to load (optional)
            enable_training: Enable optional T-stage learning (default: False)
            collect_metrics: Enable metrics collection (default: True)
            learning_algorithm: Learning algorithm ("basic", "statistical", "adaptive")
            learning_rate: Base learning rate for statistical algorithms
            convergence_threshold: Threshold for convergence detection
            enable_cross_function_learning: Enable learning across functions
            performance_tracking: Enable advanced performance tracking
        """
        self.retries = retries
        self.timeout = timeout
        self.domain = domain
        self.enable_training = enable_training
        self.collect_metrics = collect_metrics

        # Advanced learning configuration
        self.learning_algorithm = learning_algorithm
        self.learning_rate = learning_rate
        self.convergence_threshold = convergence_threshold
        self.enable_cross_function_learning = enable_cross_function_learning
        self.performance_tracking = performance_tracking

        # Enhanced Training stage parameters (Phase T2)
        self.feedback_mode = "real_world"  # "real_world", "simulation", "hybrid", "safe_testing"
        self.enable_simulation_feedback = False
        self.simulation_confidence_threshold = 0.6


class POEMetrics:
    """Simple metrics collection for POET pipeline monitoring."""

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

    def get_stats(self) -> dict[str, Any]:
        """Get current metrics statistics."""
        return {
            "total_executions": self.total_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "failure_rate": self.failed_executions / max(self.total_executions, 1),
            "avg_execution_time": self.avg_execution_time,
            "total_retries": self.retry_count,
        }


class POETExecutor(Loggable):
    """
    Unified POET executor implementing Perceive → Operate → Enforce pipeline.

    This implementation provides the core value of POET while supporting both
    basic and advanced T-stage learning algorithms.
    """

    def __init__(self, config: POETConfig):
        super().__init__()
        self.config = config
        self.domain_plugin = self._load_domain_plugin()
        self.function_name = None  # Set when wrapping a function
        self.metrics = POEMetrics() if config.collect_metrics else None

        # Optional T-stage components (loaded only if training enabled)
        self.parameters = None

        # Advanced learning components (only for statistical/adaptive algorithms)
        self.online_learner = None
        self.performance_tracker = None

        if config.enable_training:
            self.function_name = None  # Will be set later

            # Initialize advanced learning components if needed
            if config.learning_algorithm != "basic":
                self._initialize_advanced_learning()

    def __call__(self, func: Callable) -> Callable:
        """Wrap a function with POET enhancement."""
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
                self.error(f"POET execution failed for {func.__name__}: {e}")

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
                                "stage": getattr(e, "stage", "unknown") if isinstance(e, POETError) else "unknown",
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
                if not isinstance(e, POETError):
                    context = create_context(function_name=func.__name__, domain=self.config.domain, execution_time=execution_time)
                    raise wrap_poe_error(func.__name__, "operate", e, context)
                else:
                    raise

        # Attach the executor to the wrapped function for introspection
        poe_wrapper._poet_executor = self

        return poe_wrapper

    def _perceive(self, args, kwargs) -> dict[str, Any]:
        """
        P: Perceive - Input processing with domain intelligence.

        This stage analyzes and optimizes inputs before execution.
        """
        try:
            if self.domain_plugin:
                self.debug("Applying domain-specific input processing")
                
                # Set context for learning-enabled plugins
                if hasattr(self.domain_plugin, 'set_current_context'):
                    self.domain_plugin.set_current_context(
                        self.function_name or 'unknown',
                        self.config.domain or 'generic'
                    )
                
                return self.domain_plugin.process_inputs(args, kwargs)

            # Default input structure
            return {"args": args, "kwargs": kwargs}

        except Exception as e:
            self.warning(f"Perceive stage failed, using original inputs: {e}")
            return {"args": args, "kwargs": kwargs}

    def _operate_with_retry(self, func: Callable, perceived_input: dict[str, Any]) -> dict[str, Any]:
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

    def _enforce(self, operation_result: dict[str, Any], perceived_input: dict[str, Any]) -> Any:
        """
        E: Enforce - Output validation and quality assurance.

        This stage validates the operation result and applies domain-specific
        quality checks before returning the final result.
        """
        try:
            if self.domain_plugin:
                self.debug("Applying domain-specific output validation")
                
                # Provide execution context for learning-enabled plugins
                context = {
                    "perceived_input": perceived_input,
                    "execution_time": operation_result.get("execution_time", 0.0),
                    "attempts": operation_result.get("attempt", 1),
                    "success": operation_result.get("success", False)
                }
                
                return self.domain_plugin.validate_output(operation_result.get("result"), context)

            # Basic validation - ensure we have a successful result
            if operation_result.get("success", False):
                return operation_result["result"]
            else:
                raise ValueError("Operation did not complete successfully")

        except Exception as e:
            self.warning(f"Enforce stage failed: {e}")
            # Return raw result if validation fails
            return operation_result.get("result") if isinstance(operation_result, dict) else operation_result

    def _initialize_advanced_learning(self):
        """Initialize advanced learning components for statistical/adaptive algorithms."""
        try:
            # Import advanced learning components (lazy import to avoid circular dependencies)
            from .learning.metrics import PerformanceTracker
            from .learning.online_learner import OnlineLearner

            # Initialize online learner with configuration
            self.online_learner = OnlineLearner(
                base_learning_rate=self.config.learning_rate, confidence_threshold=self.config.convergence_threshold
            )

            # Initialize performance tracker if enabled
            if self.config.performance_tracking:
                self.performance_tracker = PerformanceTracker()

            self.info(f"Advanced T-stage learning initialized with {self.config.learning_algorithm} algorithm")

        except ImportError as e:
            self.warning(f"Advanced learning components not available: {e}")
            # Fall back to basic learning
            self.online_learner = None
            self.performance_tracker = None
        except Exception as e:
            self.warning(f"Failed to initialize advanced learning: {e}")
            # Fall back to basic learning
            self.online_learner = None
            self.performance_tracker = None

    def _train(self, perceived_input: dict[str, Any], execution_result: dict[str, Any]):
        """
        T: Train - Unified learning and parameter optimization.

        This stage supports multiple learning algorithms:
        - basic: Simple heuristic learning (original implementation)
        - statistical: Advanced online learning with gradient estimation
        - adaptive: Self-optimizing learning strategy selection
        """
        if not self.config.enable_training:
            return

        try:
            # Apply appropriate learning algorithm
            if self.config.learning_algorithm == "basic":
                self._train_basic(perceived_input, execution_result)
            elif self.config.learning_algorithm == "statistical" and self.online_learner:
                self._train_statistical(perceived_input, execution_result)
            elif self.config.learning_algorithm == "adaptive" and self.online_learner:
                self._train_adaptive(perceived_input, execution_result)
            else:
                # Fall back to basic learning
                self._train_basic(perceived_input, execution_result)

        except Exception as e:
            self.warning(f"T-stage learning failed: {e}")

    def _train_basic(self, perceived_input: dict[str, Any], execution_result: dict[str, Any]):
        """Basic heuristic learning implementation."""
        if not self.parameters:
            return

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

    def _train_statistical(self, perceived_input: dict[str, Any], execution_result: dict[str, Any]):
        """Statistical learning implementation using online learning algorithms."""
        try:
            from .learning.online_learner import ExecutionFeedback

            # Create rich feedback for advanced learning
            feedback = ExecutionFeedback(
                function_name=self.function_name or "unknown",
                execution_id=f"{int(time.time() * 1000)}",
                success=execution_result.get("success", False),
                execution_time=execution_result.get("execution_time", 0.0),
                output_quality=self._calculate_output_quality(execution_result),
                error_type=execution_result.get("error"),
                parameters_used=getattr(self, "parameters", {}) or {},
                performance_metrics={},
            )

            # Update parameters using online learning
            current_params = getattr(self, "parameters", {}) or {}
            if self.online_learner:
                updated_params = self.online_learner.update_parameters(feedback, current_params)
            else:
                updated_params = current_params

            # Update stored parameters
            if updated_params != current_params:
                self.parameters = updated_params
                self._save_parameters()
                self.debug(f"Statistical learning updated {len(updated_params)} parameters")

            # Record performance for tracking
            if self.performance_tracker:
                self.performance_tracker.record_performance(
                    function_name=feedback.function_name,
                    parameter_values=feedback.parameters_used,
                    performance_score=feedback.output_quality,
                    execution_time=feedback.execution_time,
                    success=feedback.success,
                    error_type=feedback.error_type,
                )

            # Send feedback to domain plugin for plugin-specific learning
            if self.domain_plugin and hasattr(self.domain_plugin, 'receive_feedback'):
                plugin_feedback = {
                    "function_name": feedback.function_name,
                    "success": feedback.success,
                    "execution_time": feedback.execution_time,
                    "output_quality": feedback.output_quality,
                    "error_type": feedback.error_type,
                    "parameters_used": feedback.parameters_used,
                    "perceived_input": perceived_input,
                    "execution_result": execution_result
                }
                self.domain_plugin.receive_feedback(plugin_feedback)

        except Exception as e:
            self.warning(f"Statistical learning failed, falling back to basic: {e}")
            self._train_basic(perceived_input, execution_result)

    def _train_adaptive(self, perceived_input: dict[str, Any], execution_result: dict[str, Any]):
        """Adaptive learning implementation (future implementation)."""
        self.debug("Adaptive learning not yet implemented, using statistical learning")
        self._train_statistical(perceived_input, execution_result)

    def _calculate_output_quality(self, execution_result: dict[str, Any]) -> float:
        """Calculate output quality score for learning feedback."""
        if not execution_result.get("success", False):
            return 0.0

        # Basic quality calculation based on success and efficiency
        quality = 0.5  # Base score for success

        # Adjust based on execution time (faster is better, up to a point)
        execution_time = execution_result.get("execution_time", 0)
        if execution_time > 0:
            if execution_time < self.config.timeout * 0.5:
                quality += 0.3  # Bonus for fast execution
            elif execution_time > self.config.timeout * 0.9:
                quality -= 0.2  # Penalty for slow execution

        # Adjust based on number of attempts (fewer is better)
        attempts = execution_result.get("attempts", 1)
        if attempts == 1:
            quality += 0.2  # Bonus for success on first try
        elif attempts > 3:
            quality -= 0.1  # Penalty for many retries

        return max(0.0, min(1.0, quality))

    def _load_domain_plugin(self):
        """Load domain-specific plugin if specified."""
        if not self.config.domain:
            return None

        try:
            from .plugins import PLUGIN_REGISTRY

            plugin_instance = PLUGIN_REGISTRY.get_plugin(self.config.domain)
            if plugin_instance:
                self.debug(f"Loaded plugin: {self.config.domain}")
                return plugin_instance
            else:
                available_plugins = PLUGIN_REGISTRY.list_plugins()
                self.warning(f"Unknown plugin: {self.config.domain}. Available plugins: {available_plugins}")
                return None

        except ImportError as e:
            self.warning(f"Could not load plugin for {self.config.domain}: {e}")
            return None

    def _load_parameters(self):
        """Load parameters from JSON storage (T-stage only)."""
        if not self.config.enable_training:
            return None

        try:
            params_file = self._get_parameters_file()
            if params_file.exists():
                with open(params_file) as f:
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
        # Store in .poet subdirectory of current working directory (project-specific)
        current_dir = Path.cwd()
        poet_dir = current_dir / ".poet"

        # Use function name and domain for unique parameter sets
        if self.function_name:
            filename = f"{self.function_name}"
            if self.config.domain:
                filename += f"_{self.config.domain}"
            filename += "_params.json"
        else:
            filename = "default_params.json"

        return poet_dir / filename

    def get_metrics(self) -> dict[str, Any] | None:
        """Get current POET execution metrics."""
        if self.metrics:
            return self.metrics.get_stats()
        return None

    def get_learning_status(self) -> dict[str, Any]:
        """Get comprehensive learning status and metrics."""
        status = {
            "learning_enabled": self.config.enable_training,
            "learning_algorithm": self.config.learning_algorithm,
            "function_name": self.function_name,
            "domain": self.config.domain,
        }

        # Basic POET metrics
        if hasattr(self, "metrics") and self.metrics:
            status["poe_metrics"] = self.metrics.get_stats()

        # Advanced learning metrics
        if self.online_learner:
            try:
                status["online_learning"] = self.online_learner.get_learning_stats()
            except Exception as e:
                self.debug(f"Failed to get online learning stats: {e}")

        if self.performance_tracker:
            try:
                status["performance_summary"] = self.performance_tracker.get_performance_summary(self.function_name)
            except Exception as e:
                self.debug(f"Failed to get performance summary: {e}")

        # Parameter convergence status
        if self.online_learner and self.function_name:
            try:
                convergence_status = {}
                current_params = getattr(self, "parameters", {}) or {}
                for param_name in current_params:
                    converged = self.online_learner.detect_convergence(param_name)
                    convergence_status[param_name] = converged
                status["convergence_status"] = convergence_status
            except Exception as e:
                self.debug(f"Failed to get convergence status: {e}")

        return status

    def get_learning_recommendations(self) -> list[str]:
        """Get actionable learning recommendations."""
        recommendations = []

        if not self.config.enable_training:
            recommendations.append("Enable training to start learning optimization")
            return recommendations

        # Get learning status
        status = self.get_learning_status()

        # Analyze online learning effectiveness
        if "online_learning" in status:
            ol_stats = status["online_learning"]
            success_rate = ol_stats.get("success_rate", 0.0)

            if success_rate < 0.5:
                recommendations.append("Low learning success rate - consider adjusting learning rate")
            elif success_rate > 0.9:
                recommendations.append("High learning success rate - learning is effective")

        # Analyze performance trends
        if "performance_summary" in status:
            perf_summary = status["performance_summary"]
            insights = perf_summary.get("insights", [])
            recommendations.extend(insights)

        # Analyze convergence
        if "convergence_status" in status:
            convergence = status["convergence_status"]
            converged_params = sum(1 for v in convergence.values() if v)
            total_params = len(convergence)

            if total_params > 0:
                convergence_rate = converged_params / total_params
                if convergence_rate > 0.8:
                    recommendations.append("Most parameters converged - learning stable")
                elif convergence_rate < 0.3:
                    recommendations.append("Low convergence rate - may need more time or tuning")

        return recommendations if recommendations else ["Learning system operating normally"]


def poet(
    retries: int = 3,
    timeout: float = 30.0,
    domain: str | None = None,
    enable_training: bool = False,
    collect_metrics: bool = True,
    # Advanced learning parameters (optional)
    learning_algorithm: str = "basic",
    learning_rate: float = 0.05,
    convergence_threshold: float = 0.01,
    enable_cross_function_learning: bool = False,
    performance_tracking: bool = True,
) -> Callable:
    """
    Unified POET decorator for enhanced function execution.

    This decorator implements the core POET (Perceive → Operate → Enforce) pipeline
    with optional T-stage (Train) functionality supporting multiple learning algorithms.

    Args:
        retries: Number of retry attempts on failure (default: 3)
        timeout: Timeout in seconds for function execution (default: 30.0)
        domain: Domain-specific plugin to load (optional)
        enable_training: Enable optional T-stage learning (default: False)
        collect_metrics: Enable metrics collection (default: True)
        learning_algorithm: Learning algorithm ("basic", "statistical", "adaptive")
        learning_rate: Base learning rate for statistical algorithms
        convergence_threshold: Threshold for convergence detection
        enable_cross_function_learning: Enable learning across functions
        performance_tracking: Enable advanced performance tracking

    Returns:
        Decorated function with POET enhancements

    Examples:
        Basic POET enhancement:
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

        With basic T-stage learning:
        ```python
        @poet(enable_training=True)
        def basic_learning():
            # + Basic parameter learning
            return result
        ```

        With advanced statistical learning:
        ```python
        @poet(
            domain="llm_optimization",
            enable_training=True,
            learning_algorithm="statistical",
            learning_rate=0.1
        )
        def enhanced_reasoning():
            # + Advanced statistical learning
            return reasoning_result
        ```
    """
    config = POETConfig(
        retries=retries,
        timeout=timeout,
        domain=domain,
        enable_training=enable_training,
        collect_metrics=collect_metrics,
        learning_algorithm=learning_algorithm,
        learning_rate=learning_rate,
        convergence_threshold=convergence_threshold,
        enable_cross_function_learning=enable_cross_function_learning,
        performance_tracking=performance_tracking,
    )
    executor = POETExecutor(config)
    return executor


# Legacy compatibility aliases
SimplePOETConfig = POETConfig
SimplePOETExecutor = POETExecutor
