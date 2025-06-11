"""
Enhanced POET Implementation with Advanced T-Stage Learning

This module extends the basic POE system with sophisticated statistical
learning algorithms, pattern recognition, and cross-function intelligence.
"""

import json
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List

from opendxa.common.mixins.loggable import Loggable
from .mvp_poet import POEConfig, POEExecutor  # Import base classes
from .learning.online_learner import OnlineLearner, ExecutionFeedback
from .learning.metrics import PerformanceTracker, LearningMetrics
from .errors import (
    POEError,
    PerceiveError,
    OperateError,
    EnforceError,
    TrainError,
    wrap_poe_error,
)


class EnhancedPOEConfig(POEConfig):
    """Enhanced configuration with advanced T-stage learning options."""

    def __init__(
        self,
        retries: int = 3,
        timeout: float = 30.0,
        domain: Optional[str] = None,
        enable_training: bool = False,
        collect_metrics: bool = True,
        # Advanced learning parameters
        learning_algorithm: str = "statistical",  # "basic", "statistical", "adaptive"
        learning_rate: float = 0.05,
        convergence_threshold: float = 0.01,
        enable_cross_function_learning: bool = False,
        performance_tracking: bool = True,
    ):

        super().__init__(retries, timeout, domain, enable_training, collect_metrics)

        # Advanced learning configuration
        self.learning_algorithm = learning_algorithm
        self.learning_rate = learning_rate
        self.convergence_threshold = convergence_threshold
        self.enable_cross_function_learning = enable_cross_function_learning
        self.performance_tracking = performance_tracking


class EnhancedPOEExecutor(POEExecutor):
    """
    Enhanced POE executor with advanced T-stage learning capabilities.

    Extends the basic POE system with:
    - Statistical online learning algorithms
    - Performance tracking and analytics
    - Cross-function intelligence sharing
    - Adaptive learning strategies
    """

    def __init__(self, config: EnhancedPOEConfig):
        # Initialize base POE system
        base_config = POEConfig(
            retries=config.retries,
            timeout=config.timeout,
            domain=config.domain,
            enable_training=config.enable_training,
            collect_metrics=config.collect_metrics,
        )
        super().__init__(base_config)

        # Enhanced configuration
        self.enhanced_config = config

        # Advanced learning components
        self.online_learner: Optional[OnlineLearner] = None
        self.performance_tracker: Optional[PerformanceTracker] = None

        # Initialize advanced learning if enabled
        if config.enable_training and config.learning_algorithm != "basic":
            self._initialize_advanced_learning()

    def _initialize_advanced_learning(self):
        """Initialize advanced learning components"""

        try:
            # Initialize online learner with configuration
            self.online_learner = OnlineLearner(
                base_learning_rate=self.enhanced_config.learning_rate, confidence_threshold=self.enhanced_config.convergence_threshold
            )

            # Initialize performance tracker if enabled
            if self.enhanced_config.performance_tracking:
                self.performance_tracker = PerformanceTracker()

            self.info("Advanced T-stage learning initialized successfully")

        except Exception as e:
            self.warning(f"Failed to initialize advanced learning: {e}")
            # Fall back to basic learning
            self.online_learner = None
            self.performance_tracker = None

    def __call__(self, func: Callable) -> Callable:
        """Wrap function with enhanced POE pipeline"""

        # Set function name for learning
        self.function_name = func.__name__

        # Initialize T-stage components if training is enabled
        if self.enhanced_config.enable_training:
            if self.enhanced_config.learning_algorithm == "basic":
                # Use basic learning from parent class
                self.parameters = self._load_parameters()
            else:
                # Advanced learning initialization handled in _initialize_advanced_learning
                pass

        @wraps(func)
        def enhanced_poe_wrapper(*args, **kwargs):
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

                # T: Enhanced Train - Advanced learning and optimization
                if self.enhanced_config.enable_training:
                    train_start = time.time()
                    try:
                        self._enhanced_train(perceived_input, execution_result, stage_timings)
                        stage_timings["train"] = time.time() - train_start
                    except Exception as learning_error:
                        stage_timings["train"] = time.time() - train_start
                        self.warning(f"Enhanced T-stage learning failed: {learning_error}")

                # Record performance metrics
                self._record_performance_metrics(perceived_input, execution_result, stage_timings)

                return enforced_result

            except Exception as e:
                execution_time = time.time() - start_time

                # Record failure for learning
                if self.enhanced_config.enable_training:
                    failure_result = {
                        "success": False,
                        "error": str(e),
                        "execution_time": execution_time,
                        "attempts": getattr(e, "attempts", 1),
                    }
                    self._enhanced_train(
                        perceived_input if "perceived_input" in locals() else {"args": args, "kwargs": kwargs},
                        failure_result,
                        stage_timings,
                    )

                self.error(f"Enhanced POE execution failed for {func.__name__}: {e}")
                raise

        return enhanced_poe_wrapper

    def _enhanced_train(self, perceived_input: Dict[str, Any], execution_result: Dict[str, Any], stage_timings: Dict[str, float]):
        """
        Enhanced T-stage with advanced learning algorithms.

        Supports multiple learning strategies:
        - Basic: Simple heuristic learning (from parent class)
        - Statistical: Advanced online learning with gradient estimation
        - Adaptive: Self-optimizing learning strategy selection
        """

        if not self.enhanced_config.enable_training:
            return

        try:
            # Create rich feedback for advanced learning
            feedback = ExecutionFeedback(
                function_name=self.function_name or "unknown",
                execution_id=f"{int(time.time() * 1000)}",
                success=execution_result.get("success", False),
                execution_time=execution_result.get("execution_time", 0.0),
                output_quality=self._calculate_output_quality(execution_result),
                error_type=execution_result.get("error"),
                parameters_used=getattr(self, "parameters", {}) or {},
                performance_metrics=stage_timings.copy(),
            )

            # Apply appropriate learning algorithm
            if self.enhanced_config.learning_algorithm == "basic":
                # Use basic learning from parent class
                self._train(perceived_input, execution_result)

            elif self.enhanced_config.learning_algorithm == "statistical" and self.online_learner:
                # Advanced statistical learning
                current_params = getattr(self, "parameters", {}) or {}
                updated_params = self.online_learner.update_parameters(feedback, current_params)

                # Update stored parameters
                if updated_params != current_params:
                    self.parameters = updated_params
                    self._save_parameters()

                    self.debug(f"Statistical learning updated {len(updated_params)} parameters")

            elif self.enhanced_config.learning_algorithm == "adaptive":
                # Adaptive learning (future implementation)
                self._adaptive_learning(feedback, perceived_input, execution_result)

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

        except Exception as e:
            self.warning(f"Enhanced T-stage learning failed: {e}")
            # Fall back to basic learning if advanced learning fails
            if hasattr(super(), "_train"):
                super()._train(perceived_input, execution_result)

    def _calculate_output_quality(self, execution_result: Dict[str, Any]) -> float:
        """Calculate output quality score for learning feedback"""

        if not execution_result.get("success", False):
            return 0.0

        # Base quality from success
        quality = 0.7

        # Adjust based on execution time (faster is better, within reason)
        exec_time = execution_result.get("execution_time", 0.0)
        if exec_time > 0:
            # Normalize execution time (assuming 1-60 second range)
            time_score = max(0.0, min(0.3, 0.3 * (10.0 / max(exec_time, 0.1))))
            quality += time_score

        # Adjust based on number of attempts (fewer is better)
        attempts = execution_result.get("attempts", 1)
        if attempts == 1:
            quality += 0.1  # Bonus for success on first try
        elif attempts > 3:
            quality -= 0.1  # Penalty for many retries

        return max(0.0, min(1.0, quality))

    def _adaptive_learning(self, feedback: ExecutionFeedback, perceived_input: Dict[str, Any], execution_result: Dict[str, Any]):
        """Adaptive learning strategy selection (future implementation)"""

        # Placeholder for adaptive learning
        # This would analyze performance patterns and select optimal learning strategies
        self.debug("Adaptive learning not yet implemented, using statistical learning")

        if self.online_learner:
            current_params = getattr(self, "parameters", {}) or {}
            updated_params = self.online_learner.update_parameters(feedback, current_params)

            if updated_params != current_params:
                self.parameters = updated_params
                self._save_parameters()

    def _record_performance_metrics(
        self, perceived_input: Dict[str, Any], execution_result: Dict[str, Any], stage_timings: Dict[str, float]
    ):
        """Record comprehensive performance metrics"""

        if not self.enhanced_config.collect_metrics:
            return

        try:
            # Record in global metrics collector if available
            from .metrics import get_global_collector

            global_collector = get_global_collector()
            global_collector.record_execution(
                function_name=self.function_name or "unknown",
                success=execution_result.get("success", False),
                total_time=execution_result.get("execution_time", 0.0),
                attempts=execution_result.get("attempts", 1),
                domain=self.enhanced_config.domain,
                stage_timings=stage_timings,
                config_info={
                    "retries": self.enhanced_config.retries,
                    "timeout": self.enhanced_config.timeout,
                    "learning_algorithm": self.enhanced_config.learning_algorithm,
                    "training_enabled": self.enhanced_config.enable_training,
                },
            )

        except Exception as e:
            self.debug(f"Failed to record performance metrics: {e}")

    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning status and metrics"""

        status = {
            "learning_enabled": self.enhanced_config.enable_training,
            "learning_algorithm": self.enhanced_config.learning_algorithm,
            "function_name": self.function_name,
            "domain": self.enhanced_config.domain,
        }

        # Basic POE metrics
        if hasattr(self, "metrics") and self.metrics:
            status["poe_metrics"] = self.metrics.get_stats()

        # Advanced learning metrics
        if self.online_learner:
            status["online_learning"] = self.online_learner.get_learning_stats()

        if self.performance_tracker:
            status["performance_summary"] = self.performance_tracker.get_performance_summary(self.function_name)

        # Parameter convergence status
        if self.online_learner and self.function_name:
            convergence_status = {}
            current_params = getattr(self, "parameters", {}) or {}
            for param_name in current_params:
                converged = self.online_learner.detect_convergence(param_name)
                convergence_status[param_name] = converged
            status["convergence_status"] = convergence_status

        return status

    def get_learning_recommendations(self) -> List[str]:
        """Get actionable learning recommendations"""

        recommendations = []

        if not self.enhanced_config.enable_training:
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


def enhanced_poet(
    retries: int = 3,
    timeout: float = 30.0,
    domain: Optional[str] = None,
    enable_training: bool = False,
    collect_metrics: bool = True,
    learning_algorithm: str = "statistical",
    learning_rate: float = 0.05,
    convergence_threshold: float = 0.01,
) -> Callable:
    """
    Enhanced POET decorator with advanced T-stage learning.

    Args:
        retries: Number of retry attempts on failure
        timeout: Timeout in seconds for function execution
        domain: Domain-specific plugin to load
        enable_training: Enable T-stage learning
        collect_metrics: Enable metrics collection
        learning_algorithm: Learning algorithm ("basic", "statistical", "adaptive")
        learning_rate: Base learning rate for statistical algorithms
        convergence_threshold: Threshold for convergence detection

    Returns:
        Decorated function with enhanced POE pipeline

    Examples:
        Basic enhanced learning:
        ```python
        @enhanced_poet(enable_training=True)
        def my_function():
            return "result"
        ```

        Advanced statistical learning:
        ```python
        @enhanced_poet(
            domain="llm_optimization",
            enable_training=True,
            learning_algorithm="statistical",
            learning_rate=0.1
        )
        def reasoning_function():
            return "optimized result"
        ```
    """

    config = EnhancedPOEConfig(
        retries=retries,
        timeout=timeout,
        domain=domain,
        enable_training=enable_training,
        collect_metrics=collect_metrics,
        learning_algorithm=learning_algorithm,
        learning_rate=learning_rate,
        convergence_threshold=convergence_threshold,
    )

    executor = EnhancedPOEExecutor(config)
    return executor


# Maintain backwards compatibility
def poet_with_advanced_learning(*args, **kwargs):
    """Alias for enhanced_poet with advanced learning enabled by default"""
    kwargs.setdefault("enable_training", True)
    kwargs.setdefault("learning_algorithm", "statistical")
    return enhanced_poet(*args, **kwargs)
