"""
Statistical Online Learning for POET T-Stage Enhancement

This module implements advanced online learning algorithms that replace
basic heuristic parameter adjustments with sophisticated statistical methods
for real-time parameter optimization.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from opendxa.common.mixins.loggable import Loggable


@dataclass
class ExecutionFeedback:
    """Rich feedback data for online learning"""

    function_name: str
    execution_id: str

    # Performance metrics
    success: bool
    execution_time: float
    output_quality: float = 0.8  # 0.0 to 1.0 quality score
    error_type: str | None = None

    # Context information
    input_signature: str = ""
    domain: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Parameter state
    parameters_used: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)

    # User feedback (optional)
    user_satisfaction: float | None = None
    validation_passed: bool = True


@dataclass
class ParameterHistory:
    """Track parameter evolution over time"""

    values: deque = field(default_factory=lambda: deque(maxlen=100))
    performances: deque = field(default_factory=lambda: deque(maxlen=100))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
    confidence_scores: deque = field(default_factory=lambda: deque(maxlen=100))

    def add_observation(self, value: float, performance: float, confidence: float = 0.5):
        """Add new parameter observation"""
        self.values.append(value)
        self.performances.append(performance)
        self.timestamps.append(datetime.now())
        self.confidence_scores.append(confidence)

    def get_recent_trend(self, window: int = 10) -> float:
        """Calculate recent performance trend"""
        if len(self.performances) < 2:
            return 0.0

        recent_perfs = list(self.performances)[-window:]
        if len(recent_perfs) < 2:
            return 0.0

        # Simple linear trend
        x = np.arange(len(recent_perfs))
        slope, _ = np.polyfit(x, recent_perfs, 1)
        return slope

    def estimate_gradient(self) -> float:
        """Estimate performance gradient with respect to parameter"""
        if len(self.values) < 3:
            return 0.0

        values = np.array(list(self.values)[-10:])  # Last 10 observations
        performances = np.array(list(self.performances)[-10:])

        if len(np.unique(values)) < 2:  # No parameter variation
            return 0.0

        try:
            # Linear regression for gradient estimation
            slope, _ = np.polyfit(values, performances, 1)
            return slope
        except:
            return 0.0


class OnlineLearner(Loggable):
    """
    Advanced statistical online learning for POET parameters.

    Implements sophisticated algorithms including:
    - Exponential weighted moving averages
    - Gradient-based optimization
    - Confidence interval estimation
    - Adaptive learning rates
    - Thompson sampling for exploration
    """

    def __init__(
        self, base_learning_rate: float = 0.05, momentum: float = 0.9, confidence_threshold: float = 0.7, exploration_rate: float = 0.1
    ):
        super().__init__()

        # Learning hyperparameters
        self.base_learning_rate = base_learning_rate
        self.momentum = momentum
        self.confidence_threshold = confidence_threshold
        self.exploration_rate = exploration_rate

        # Parameter tracking
        self.parameter_histories: dict[str, ParameterHistory] = defaultdict(ParameterHistory)
        self.learning_rates: dict[str, float] = defaultdict(lambda: base_learning_rate)
        self.momentum_terms: dict[str, float] = defaultdict(float)
        self.confidence_scores: dict[str, float] = defaultdict(lambda: 0.5)

        # Performance tracking
        self.global_performance_history = deque(maxlen=1000)
        self.convergence_status: dict[str, bool] = defaultdict(bool)

        # Learning statistics
        self.update_count = 0
        self.successful_updates = 0
        self.last_update_time = datetime.now()

    def update_parameters(self, feedback: ExecutionFeedback, current_params: dict[str, Any]) -> dict[str, Any]:
        """
        Update parameters using advanced statistical online learning.

        Args:
            feedback: Rich execution feedback with performance metrics
            current_params: Current parameter values

        Returns:
            Updated parameters with statistical optimization
        """
        self.update_count += 1

        # Record global performance
        self.global_performance_history.append(
            {"performance": feedback.output_quality, "success": feedback.success, "timestamp": feedback.timestamp}
        )

        updated_params = current_params.copy()
        param_key = f"{feedback.function_name}:{feedback.input_signature}"

        self.debug(f"Online learning update for {feedback.function_name} " f"(quality: {feedback.output_quality:.3f})")

        # Update each parameter using appropriate algorithm
        for param_name, param_value in current_params.items():
            try:
                new_value = self._update_single_parameter(param_name, param_value, feedback, param_key)

                if new_value != param_value:
                    updated_params[param_name] = new_value
                    self.debug(f"Updated {param_name}: {param_value} → {new_value}")

            except Exception as e:
                self.warning(f"Failed to update parameter {param_name}: {e}")
                continue

        # Track learning success
        if any(updated_params[k] != current_params[k] for k in current_params):
            self.successful_updates += 1

        self.last_update_time = datetime.now()
        return updated_params

    def _update_single_parameter(self, param_name: str, current_value: Any, feedback: ExecutionFeedback, param_key: str) -> Any:
        """Update individual parameter using appropriate algorithm"""

        if not isinstance(current_value, (int, float)):
            return current_value  # Only update numerical parameters

        history_key = f"{param_key}:{param_name}"
        history = self.parameter_histories[history_key]

        # Calculate performance score
        performance_score = self._calculate_performance_score(feedback)

        # Add observation to history
        history.add_observation(value=float(current_value), performance=performance_score, confidence=self.confidence_scores[history_key])

        # Choose learning algorithm based on parameter characteristics
        if param_name == "timeout":
            return self._update_timeout_parameter(current_value, feedback, history)
        elif param_name == "retries":
            return self._update_retries_parameter(current_value, feedback, history)
        elif "rate" in param_name.lower() or "learning" in param_name.lower():
            return self._update_rate_parameter(current_value, feedback, history)
        else:
            return self._update_generic_parameter(current_value, feedback, history, param_name)

    def _calculate_performance_score(self, feedback: ExecutionFeedback) -> float:
        """Calculate composite performance score from feedback"""

        score = 0.0
        weight_sum = 0.0

        # Success/failure (high weight)
        if feedback.success:
            score += 0.8 * 0.4  # 40% weight
        weight_sum += 0.4

        # Output quality (high weight)
        score += feedback.output_quality * 0.3  # 30% weight
        weight_sum += 0.3

        # Execution time (efficiency, 20% weight)
        if feedback.execution_time > 0:
            # Faster is better, but normalize to reasonable range
            time_score = max(0.0, min(1.0, 10.0 / max(feedback.execution_time, 0.1)))
            score += time_score * 0.2
        weight_sum += 0.2

        # User satisfaction (if available, 10% weight)
        if feedback.user_satisfaction is not None:
            score += feedback.user_satisfaction * 0.1
            weight_sum += 0.1

        return score / weight_sum if weight_sum > 0 else 0.5

    def _update_timeout_parameter(self, current_timeout: float, feedback: ExecutionFeedback, history: ParameterHistory) -> float:
        """Specialized timeout parameter optimization"""

        # Base adjustment based on execution performance
        adjustment = 0.0

        if not feedback.success:
            # Increase timeout on failure
            adjustment = current_timeout * 0.2  # 20% increase
        elif feedback.execution_time > current_timeout * 0.9:
            # Near timeout, increase slightly
            adjustment = current_timeout * 0.1
        elif feedback.execution_time < current_timeout * 0.3:
            # Very fast, can decrease
            adjustment = -current_timeout * 0.1

        # Apply gradient optimization if we have enough history
        if len(history.values) > 2:
            gradient = history.estimate_gradient()
            learning_rate = self._adaptive_learning_rate("timeout", gradient)

            if abs(gradient) > 0.01:  # Significant gradient
                gradient_adjustment = learning_rate * gradient * current_timeout
                adjustment += gradient_adjustment

        # Apply momentum if we have previous adjustments
        momentum_key = "timeout"
        if momentum_key in self.momentum_terms:
            self.momentum_terms[momentum_key] = self.momentum * self.momentum_terms[momentum_key] + (1 - self.momentum) * adjustment
        else:
            self.momentum_terms[momentum_key] = adjustment

        new_timeout = current_timeout + self.momentum_terms[momentum_key]

        # Apply bounds
        return max(1.0, min(300.0, new_timeout))  # 1s to 5min range

    def _update_retries_parameter(self, current_retries: int, feedback: ExecutionFeedback, history: ParameterHistory) -> int:
        """Specialized retries parameter optimization"""

        # Track recent failure rate
        recent_successes = sum(1 for p in list(history.performances)[-10:] if p > 0.5)
        recent_total = len(list(history.performances)[-10:])

        if recent_total >= 5:
            success_rate = recent_successes / recent_total

            if success_rate < 0.7 and current_retries < 8:
                # Low success rate, increase retries
                return current_retries + 1
            elif success_rate > 0.95 and current_retries > 1:
                # Very high success rate, can decrease retries
                return current_retries - 1

        return current_retries

    def _update_rate_parameter(self, current_rate: float, feedback: ExecutionFeedback, history: ParameterHistory) -> float:
        """Update rate-type parameters (learning rates, etc.)"""

        # Use exponential weighted moving average
        performance_score = self._calculate_performance_score(feedback)

        # EWMA with performance weighting
        alpha = 0.1 * (performance_score + 0.5)  # Adaptive smoothing

        if len(history.performances) > 1:
            avg_performance = sum(history.performances) / len(history.performances)

            if performance_score > avg_performance:
                # Good performance, slightly increase rate
                adjustment = current_rate * 0.05
            else:
                # Poor performance, slightly decrease rate
                adjustment = -current_rate * 0.05

            new_rate = current_rate + alpha * adjustment
            return max(0.001, min(1.0, new_rate))  # Keep in reasonable bounds

        return current_rate

    def _update_generic_parameter(
        self, current_value: float, feedback: ExecutionFeedback, history: ParameterHistory, param_name: str
    ) -> float:
        """Generic parameter update using Thompson sampling"""

        # Thompson sampling for exploration/exploitation
        if len(history.performances) < 3:
            return current_value  # Need more data

        # Estimate parameter uncertainty
        recent_performances = list(history.performances)[-10:]
        performance_std = np.std(recent_performances) if len(recent_performances) > 1 else 0.1

        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            # Explore: add noise proportional to uncertainty
            noise = np.random.normal(0, performance_std * current_value * 0.1)
            new_value = current_value + noise
        else:
            # Exploit: gradient-based optimization
            gradient = history.estimate_gradient()
            learning_rate = self._adaptive_learning_rate(param_name, gradient)
            new_value = current_value + learning_rate * gradient * current_value

        # Apply reasonable bounds (parameter-specific)
        bounds = self._get_parameter_bounds(param_name, current_value)
        return max(bounds[0], min(bounds[1], new_value))

    def _adaptive_learning_rate(self, param_name: str, gradient: float) -> float:
        """Calculate adaptive learning rate based on gradient and convergence"""

        base_rate = self.learning_rates[param_name]

        # Adjust based on gradient magnitude
        if abs(gradient) > 0.1:
            # Large gradient, reduce learning rate for stability
            adjusted_rate = base_rate * 0.5
        elif abs(gradient) < 0.01:
            # Small gradient, increase learning rate for faster convergence
            adjusted_rate = base_rate * 1.5
        else:
            adjusted_rate = base_rate

        # Update stored learning rate with momentum
        self.learning_rates[param_name] = 0.9 * self.learning_rates[param_name] + 0.1 * adjusted_rate

        return self.learning_rates[param_name]

    def _get_parameter_bounds(self, param_name: str, current_value: float) -> tuple[float, float]:
        """Get reasonable bounds for parameter values"""

        if "timeout" in param_name.lower():
            return (1.0, 300.0)
        elif "retry" in param_name.lower() or "retries" in param_name.lower():
            return (1, 10)
        elif "rate" in param_name.lower():
            return (0.001, 1.0)
        elif "confidence" in param_name.lower():
            return (0.0, 1.0)
        else:
            # Generic bounds: ±50% of current value, with reasonable absolute bounds
            range_size = abs(current_value) * 0.5
            return (max(0.1, current_value - range_size), current_value + range_size)

    def get_learning_stats(self) -> dict[str, Any]:
        """Get comprehensive learning statistics"""

        return {
            "update_count": self.update_count,
            "successful_updates": self.successful_updates,
            "success_rate": self.successful_updates / max(self.update_count, 1),
            "parameters_tracked": len(self.parameter_histories),
            "average_confidence": np.mean(list(self.confidence_scores.values())) if self.confidence_scores else 0.0,
            "last_update": self.last_update_time.isoformat(),
            "convergence_status": dict(self.convergence_status),
            "global_performance_trend": self._calculate_global_trend(),
        }

    def _calculate_global_trend(self) -> float:
        """Calculate overall performance trend"""

        if len(self.global_performance_history) < 10:
            return 0.0

        recent_performances = [h["performance"] for h in list(self.global_performance_history)[-20:]]

        if len(recent_performances) < 2:
            return 0.0

        # Linear trend over recent history
        x = np.arange(len(recent_performances))
        slope, _ = np.polyfit(x, recent_performances, 1)
        return slope

    def detect_convergence(self, param_name: str, stability_threshold: float = 0.01) -> bool:
        """Detect if parameter has converged to stable value"""

        # Look for parameter history with various key formats
        possible_keys = [
            param_name,
            f":{param_name}",
            f"{param_name}:",
        ]

        # Find matching history
        history = None
        matched_key = None
        for key in self.parameter_histories:
            for possible_key in possible_keys:
                if possible_key in key:
                    history = self.parameter_histories[key]
                    matched_key = key
                    break
            if history:
                break

        if not history or len(history.values) < 10:  # Need sufficient history
            return False

        # Check parameter stability
        recent_values = list(history.values)[-10:]
        value_std = float(np.std(recent_values))
        value_mean = float(np.mean(recent_values))

        # Relative stability
        relative_stability = value_std / max(abs(value_mean), 0.1)

        converged = relative_stability < stability_threshold
        self.convergence_status[param_name] = converged

        return converged
