"""
Learning Metrics and Performance Tracking for POET T-Stage

This module provides comprehensive metrics collection and analysis
for monitoring the effectiveness of advanced learning algorithms.
"""

import json
import math
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from opendxa.common.mixins.loggable import Loggable


@dataclass
class LearningMetrics:
    """Comprehensive learning performance metrics"""

    # Basic metrics
    total_updates: int = 0
    successful_updates: int = 0
    convergence_rate: float = 0.0
    average_improvement: float = 0.0

    # Performance metrics
    parameter_stability: dict[str, float] = field(default_factory=dict)
    learning_efficiency: float = 0.0
    prediction_accuracy: float = 0.0

    # Temporal metrics
    convergence_time: float | None = None
    learning_velocity: float = 0.0
    performance_trend: float = 0.0

    # Advanced metrics
    exploration_exploitation_ratio: float = 0.5
    confidence_intervals: dict[str, tuple[float, float]] = field(default_factory=dict)
    cross_function_benefits: float = 0.0

    # Metadata
    measurement_window: timedelta = field(default_factory=lambda: timedelta(hours=24))
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["measurement_window"] = self.measurement_window.total_seconds()
        data["last_updated"] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearningMetrics":
        """Create from dictionary"""
        data["measurement_window"] = timedelta(seconds=data.get("measurement_window", 86400))
        data["last_updated"] = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        return cls(**data)


@dataclass
class PerformanceSnapshot:
    """Point-in-time performance measurement"""

    timestamp: datetime
    function_name: str
    parameter_values: dict[str, Any]
    performance_score: float
    execution_time: float
    success: bool
    error_type: str | None = None
    context_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class PerformanceTracker(Loggable):
    """
    Advanced performance tracking and analysis for learning systems.

    Provides comprehensive monitoring of learning effectiveness,
    parameter evolution, and performance trends.
    """

    def __init__(self, storage_path: str | None = None, window_hours: int = 168):  # 1 week default
        super().__init__()

        # Storage configuration
        self.storage_path = Path(storage_path or ".poet/metrics").resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Tracking configuration
        self.window_hours = window_hours
        self.measurement_window = timedelta(hours=window_hours)

        # Performance data
        self.performance_history: deque = deque(maxlen=10000)
        self.parameter_evolution: dict[str, list[PerformanceSnapshot]] = defaultdict(list)
        self.baseline_performance: dict[str, float] = {}

        # Learning effectiveness tracking
        self.improvement_tracking: dict[str, list[float]] = defaultdict(list)
        self.convergence_tracking: dict[str, list[datetime]] = defaultdict(list)
        self.prediction_accuracy_history: deque = deque(maxlen=1000)

        # Statistical aggregates
        self.performance_statistics: dict[str, dict[str, float]] = defaultdict(dict)
        self.learning_velocity_cache: dict[str, float] = {}

        # Load existing data
        self._load_historical_data()

    def record_performance(
        self,
        function_name: str,
        parameter_values: dict[str, Any],
        performance_score: float,
        execution_time: float,
        success: bool,
        error_type: str | None = None,
        context_signature: str = "",
    ) -> None:
        """Record a performance measurement"""

        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            function_name=function_name,
            parameter_values=parameter_values.copy(),
            performance_score=performance_score,
            execution_time=execution_time,
            success=success,
            error_type=error_type,
            context_signature=context_signature,
        )

        # Add to history
        self.performance_history.append(snapshot)
        self.parameter_evolution[function_name].append(snapshot)

        # Update baseline if this is the first measurement
        if function_name not in self.baseline_performance:
            self.baseline_performance[function_name] = performance_score

        # Track improvement
        baseline = self.baseline_performance[function_name]
        improvement = (performance_score - baseline) / max(baseline, 0.1)
        self.improvement_tracking[function_name].append(improvement)

        # Update statistics
        self._update_performance_statistics(function_name, snapshot)

        self.debug(f"Recorded performance for {function_name}: " f"score={performance_score:.3f}, time={execution_time:.3f}s")

    def record_parameter_update(
        self,
        function_name: str,
        old_params: dict[str, Any],
        new_params: dict[str, Any],
        predicted_improvement: float,
        actual_improvement: float,
    ) -> None:
        """Record learning algorithm effectiveness"""

        # Track prediction accuracy
        if predicted_improvement != 0:
            accuracy = 1.0 - abs(actual_improvement - predicted_improvement) / abs(predicted_improvement)
            self.prediction_accuracy_history.append(max(0.0, min(1.0, accuracy)))

        # Detect convergence events
        if self._detect_convergence_event(function_name, old_params, new_params):
            self.convergence_tracking[function_name].append(datetime.now())

        self.debug(f"Parameter update for {function_name}: " f"predicted={predicted_improvement:.3f}, actual={actual_improvement:.3f}")

    def calculate_learning_metrics(self, function_name: str | None = None) -> LearningMetrics:
        """Calculate comprehensive learning metrics"""

        # Filter data by function if specified
        if function_name:
            snapshots = self.parameter_evolution.get(function_name, [])
        else:
            snapshots = list(self.performance_history)

        # Filter by time window
        cutoff_time = datetime.now() - self.measurement_window
        recent_snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]

        if not recent_snapshots:
            return LearningMetrics()

        metrics = LearningMetrics()

        # Basic metrics
        metrics.total_updates = len(recent_snapshots)
        metrics.successful_updates = sum(1 for s in recent_snapshots if s.success)

        # Performance improvement
        improvements = []
        if function_name and function_name in self.improvement_tracking:
            improvements = self.improvement_tracking[function_name][-100:]  # Recent improvements
        elif not function_name:
            # Global improvements
            for func_improvements in self.improvement_tracking.values():
                improvements.extend(func_improvements[-50:])  # Recent from each function

        if improvements:
            metrics.average_improvement = np.mean(improvements)
            metrics.performance_trend = self._calculate_trend(improvements)

        # Convergence rate
        convergence_events = []
        if function_name and function_name in self.convergence_tracking:
            convergence_events = self.convergence_tracking[function_name]
        elif not function_name:
            for func_events in self.convergence_tracking.values():
                convergence_events.extend(func_events)

        recent_convergences = [e for e in convergence_events if e >= cutoff_time]
        metrics.convergence_rate = len(recent_convergences) / max(metrics.total_updates, 1)

        # Parameter stability
        metrics.parameter_stability = self._calculate_parameter_stability(recent_snapshots)

        # Learning efficiency (improvement per update)
        if metrics.total_updates > 0 and improvements:
            metrics.learning_efficiency = abs(metrics.average_improvement) / metrics.total_updates

        # Prediction accuracy
        if self.prediction_accuracy_history:
            metrics.prediction_accuracy = np.mean(list(self.prediction_accuracy_history)[-100:])

        # Convergence time (median time to convergence)
        if convergence_events:
            convergence_times = []
            for func_name, func_snapshots in self.parameter_evolution.items():
                func_events = self.convergence_tracking.get(func_name, [])
                if func_events and func_snapshots:
                    first_snapshot = min(func_snapshots, key=lambda s: s.timestamp)
                    for event in func_events:
                        time_to_convergence = (event - first_snapshot.timestamp).total_seconds()
                        convergence_times.append(time_to_convergence)

            if convergence_times:
                metrics.convergence_time = np.median(convergence_times)

        # Learning velocity (rate of performance improvement)
        metrics.learning_velocity = self._calculate_learning_velocity(recent_snapshots)

        # Confidence intervals for key parameters
        metrics.confidence_intervals = self._calculate_confidence_intervals(recent_snapshots)

        metrics.last_updated = datetime.now()
        return metrics

    def _update_performance_statistics(self, function_name: str, snapshot: PerformanceSnapshot) -> None:
        """Update running performance statistics"""

        stats = self.performance_statistics[function_name]

        # Running averages
        if "count" not in stats:
            stats["count"] = 0
            stats["sum_performance"] = 0.0
            stats["sum_execution_time"] = 0.0
            stats["sum_squared_performance"] = 0.0

        stats["count"] += 1
        stats["sum_performance"] += snapshot.performance_score
        stats["sum_execution_time"] += snapshot.execution_time
        stats["sum_squared_performance"] += snapshot.performance_score**2

        # Calculate derived statistics
        n = stats["count"]
        stats["mean_performance"] = stats["sum_performance"] / n
        stats["mean_execution_time"] = stats["sum_execution_time"] / n

        if n > 1:
            variance = (stats["sum_squared_performance"] / n) - (stats["mean_performance"] ** 2)
            stats["std_performance"] = math.sqrt(max(0, variance))
        else:
            stats["std_performance"] = 0.0

    def _calculate_parameter_stability(self, snapshots: list[PerformanceSnapshot]) -> dict[str, float]:
        """Calculate stability scores for parameters"""

        stability_scores = {}

        # Group by parameter
        param_evolution = defaultdict(list)
        for snapshot in snapshots:
            for param_name, param_value in snapshot.parameter_values.items():
                if isinstance(param_value, (int, float)):
                    param_evolution[param_name].append(param_value)

        # Calculate stability as inverse of normalized standard deviation
        for param_name, values in param_evolution.items():
            if len(values) > 1:
                mean_val = np.mean(values)
                std_val = np.std(values)
                if mean_val != 0:
                    coefficient_of_variation = std_val / abs(mean_val)
                    stability_scores[param_name] = 1.0 / (1.0 + coefficient_of_variation)
                else:
                    stability_scores[param_name] = 1.0 if std_val == 0 else 0.0
            else:
                stability_scores[param_name] = 1.0

        return stability_scores

    def _calculate_learning_velocity(self, snapshots: list[PerformanceSnapshot]) -> float:
        """Calculate rate of learning (performance improvement over time)"""

        if len(snapshots) < 2:
            return 0.0

        # Sort by timestamp
        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)

        # Calculate performance trend over time
        timestamps = [(s.timestamp - sorted_snapshots[0].timestamp).total_seconds() for s in sorted_snapshots]
        performances = [s.performance_score for s in sorted_snapshots]

        if len(set(timestamps)) < 2:  # No time variation
            return 0.0

        try:
            # Linear regression for velocity
            slope, _ = np.polyfit(timestamps, performances, 1)
            return slope  # Performance improvement per second
        except:
            return 0.0

    def _calculate_confidence_intervals(self, snapshots: list[PerformanceSnapshot]) -> dict[str, tuple[float, float]]:
        """Calculate confidence intervals for parameter values"""

        confidence_intervals = {}

        # Group by parameter
        param_values = defaultdict(list)
        for snapshot in snapshots:
            for param_name, param_value in snapshot.parameter_values.items():
                if isinstance(param_value, (int, float)):
                    param_values[param_name].append(param_value)

        # Calculate 95% confidence intervals
        for param_name, values in param_values.items():
            if len(values) > 2:
                mean_val = np.mean(values)
                std_val = np.std(values)
                margin = 1.96 * std_val / math.sqrt(len(values))  # 95% CI
                confidence_intervals[param_name] = (mean_val - margin, mean_val + margin)

        return confidence_intervals

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate linear trend of values"""

        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        try:
            slope, _ = np.polyfit(x, values, 1)
            return slope
        except:
            return 0.0

    def _detect_convergence_event(self, function_name: str, old_params: dict[str, Any], new_params: dict[str, Any]) -> bool:
        """Detect if parameters have converged (small changes)"""

        # Calculate parameter change magnitude
        total_change = 0.0
        param_count = 0

        for param_name in old_params:
            if param_name in new_params:
                old_val = old_params[param_name]
                new_val = new_params[param_name]

                if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                    if old_val != 0:
                        relative_change = abs(new_val - old_val) / abs(old_val)
                        total_change += relative_change
                        param_count += 1

        if param_count > 0:
            avg_change = total_change / param_count
            return avg_change < 0.01  # Less than 1% change indicates convergence

        return False

    def get_performance_summary(self, function_name: str | None = None) -> dict[str, Any]:
        """Get comprehensive performance summary"""

        metrics = self.calculate_learning_metrics(function_name)

        summary = {"metrics": metrics.to_dict(), "statistics": {}, "trends": {}, "insights": []}

        # Function-specific or global statistics
        if function_name and function_name in self.performance_statistics:
            summary["statistics"] = self.performance_statistics[function_name].copy()
        else:
            # Aggregate statistics
            all_stats = list(self.performance_statistics.values())
            if all_stats:
                summary["statistics"] = {
                    "total_functions": len(all_stats),
                    "total_measurements": sum(s.get("count", 0) for s in all_stats),
                    "average_performance": np.mean([s.get("mean_performance", 0) for s in all_stats]),
                    "average_execution_time": np.mean([s.get("mean_execution_time", 0) for s in all_stats]),
                }

        # Generate insights
        summary["insights"] = self._generate_insights(metrics)

        return summary

    def _generate_insights(self, metrics: LearningMetrics) -> list[str]:
        """Generate actionable insights from metrics"""

        insights = []

        # Performance insights
        if metrics.average_improvement > 0.1:
            insights.append(f"Strong learning progress: {metrics.average_improvement:.1%} average improvement")
        elif metrics.average_improvement < -0.05:
            insights.append("Performance degradation detected - consider parameter reset")

        # Convergence insights
        if metrics.convergence_rate > 0.8:
            insights.append("High convergence rate - learning algorithms are effective")
        elif metrics.convergence_rate < 0.2:
            insights.append("Low convergence rate - may need learning parameter tuning")

        # Stability insights
        avg_stability = np.mean(list(metrics.parameter_stability.values())) if metrics.parameter_stability else 0
        if avg_stability > 0.9:
            insights.append("Parameters highly stable - learning has converged")
        elif avg_stability < 0.5:
            insights.append("Parameter instability detected - increase learning smoothing")

        # Prediction accuracy insights
        if metrics.prediction_accuracy > 0.8:
            insights.append("Learning predictions highly accurate")
        elif metrics.prediction_accuracy < 0.5:
            insights.append("Learning predictions need improvement - consider algorithm tuning")

        return insights

    def _load_historical_data(self) -> None:
        """Load historical performance data"""

        try:
            history_file = self.storage_path / "performance_history.jsonl"
            if history_file.exists():
                with open(history_file) as f:
                    for line in f:
                        data = json.loads(line.strip())
                        snapshot = PerformanceSnapshot(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            function_name=data["function_name"],
                            parameter_values=data["parameter_values"],
                            performance_score=data["performance_score"],
                            execution_time=data["execution_time"],
                            success=data["success"],
                            error_type=data.get("error_type"),
                            context_signature=data.get("context_signature", ""),
                        )

                        # Only load recent data
                        cutoff = datetime.now() - timedelta(days=30)
                        if snapshot.timestamp >= cutoff:
                            self.performance_history.append(snapshot)
                            self.parameter_evolution[snapshot.function_name].append(snapshot)

                            # Update baseline
                            if snapshot.function_name not in self.baseline_performance:
                                self.baseline_performance[snapshot.function_name] = snapshot.performance_score

                self.info(f"Loaded {len(self.performance_history)} historical performance records")

        except Exception as e:
            self.warning(f"Failed to load historical data: {e}")

    def save_metrics(self) -> None:
        """Save current metrics to storage"""

        try:
            # Save performance history
            history_file = self.storage_path / "performance_history.jsonl"
            with open(history_file, "w") as f:
                for snapshot in self.performance_history:
                    f.write(json.dumps(snapshot.to_dict()) + "\n")

            # Save current metrics
            metrics = self.calculate_learning_metrics()
            metrics_file = self.storage_path / "current_metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(metrics.to_dict(), f, indent=2)

            self.debug("Learning metrics saved successfully")

        except Exception as e:
            self.warning(f"Failed to save metrics: {e}")
