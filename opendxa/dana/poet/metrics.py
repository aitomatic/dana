"""
POE Metrics Collection Framework

This module provides comprehensive metrics collection, analysis, and reporting
for the POE (Perceive → Operate → Enforce) pipeline performance monitoring.
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict, deque

from opendxa.common.mixins.loggable import Loggable


@dataclass
class POEExecutionMetrics:
    """Detailed metrics for a single POE execution."""

    # Execution identification
    function_name: str
    domain: Optional[str]
    timestamp: float

    # Execution results
    success: bool
    total_time: float
    attempts: int

    # Stage timings (in seconds)
    perceive_time: float = 0.0
    operate_time: float = 0.0
    enforce_time: float = 0.0
    train_time: Optional[float] = None

    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_stage: Optional[str] = None

    # Configuration used
    retries_configured: int = 3
    timeout_configured: float = 30.0
    training_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POEExecutionMetrics":
        """Create metrics from dictionary format."""
        return cls(**data)


class POEAggregateMetrics:
    """Aggregate metrics for POE pipeline performance analysis."""

    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0

        # Timing statistics
        self.total_execution_time = 0.0
        self.min_execution_time = float("inf")
        self.max_execution_time = 0.0

        # Stage timing aggregates
        self.perceive_time_total = 0.0
        self.operate_time_total = 0.0
        self.enforce_time_total = 0.0
        self.train_time_total = 0.0
        self.train_executions = 0

        # Retry statistics
        self.total_retries = 0
        self.max_retries_used = 0

        # Error tracking
        self.errors_by_type: Dict[str, int] = defaultdict(int)
        self.errors_by_stage: Dict[str, int] = defaultdict(int)
        self.errors_by_function: Dict[str, int] = defaultdict(int)

        # Function-specific metrics
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"executions": 0, "successes": 0, "failures": 0, "total_time": 0.0, "avg_time": 0.0}
        )

        # Domain-specific metrics
        self.domain_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"executions": 0, "successes": 0, "failures": 0, "total_time": 0.0}
        )

    def add_execution(self, metrics: POEExecutionMetrics):
        """Add execution metrics to aggregates."""
        self.total_executions += 1

        if metrics.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update timing statistics
        self.total_execution_time += metrics.total_time
        self.min_execution_time = min(self.min_execution_time, metrics.total_time)
        self.max_execution_time = max(self.max_execution_time, metrics.total_time)

        # Update stage timings
        self.perceive_time_total += metrics.perceive_time
        self.operate_time_total += metrics.operate_time
        self.enforce_time_total += metrics.enforce_time

        if metrics.train_time is not None:
            self.train_time_total += metrics.train_time
            self.train_executions += 1

        # Update retry statistics
        retries_used = metrics.attempts - 1
        self.total_retries += retries_used
        self.max_retries_used = max(self.max_retries_used, retries_used)

        # Update error statistics
        if not metrics.success and metrics.error_type:
            self.errors_by_type[metrics.error_type] += 1
        if not metrics.success and metrics.error_stage:
            self.errors_by_stage[metrics.error_stage] += 1
        if not metrics.success:
            self.errors_by_function[metrics.function_name] += 1

        # Update function statistics
        func_stats = self.function_stats[metrics.function_name]
        func_stats["executions"] += 1
        func_stats["total_time"] += metrics.total_time
        func_stats["avg_time"] = func_stats["total_time"] / func_stats["executions"]

        if metrics.success:
            func_stats["successes"] += 1
        else:
            func_stats["failures"] += 1

        # Update domain statistics
        if metrics.domain:
            domain_stats = self.domain_stats[metrics.domain]
            domain_stats["executions"] += 1
            domain_stats["total_time"] += metrics.total_time

            if metrics.success:
                domain_stats["successes"] += 1
            else:
                domain_stats["failures"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if self.total_executions == 0:
            return {"message": "No executions recorded"}

        return {
            "execution_summary": {
                "total_executions": self.total_executions,
                "successful_executions": self.successful_executions,
                "failed_executions": self.failed_executions,
                "success_rate": self.successful_executions / self.total_executions,
                "failure_rate": self.failed_executions / self.total_executions,
            },
            "timing_summary": {
                "total_time": self.total_execution_time,
                "average_time": self.total_execution_time / self.total_executions,
                "min_time": self.min_execution_time if self.min_execution_time != float("inf") else 0,
                "max_time": self.max_execution_time,
            },
            "stage_timing": {
                "average_perceive_time": self.perceive_time_total / self.total_executions,
                "average_operate_time": self.operate_time_total / self.total_executions,
                "average_enforce_time": self.enforce_time_total / self.total_executions,
                "average_train_time": self.train_time_total / max(self.train_executions, 1) if self.train_executions > 0 else None,
            },
            "retry_summary": {
                "total_retries": self.total_retries,
                "average_retries": self.total_retries / self.total_executions,
                "max_retries_used": self.max_retries_used,
            },
        }

    def get_error_analysis(self) -> Dict[str, Any]:
        """Get detailed error analysis."""
        return {
            "errors_by_type": dict(self.errors_by_type),
            "errors_by_stage": dict(self.errors_by_stage),
            "errors_by_function": dict(self.errors_by_function),
            "most_common_error_type": max(self.errors_by_type.items(), key=lambda x: x[1]) if self.errors_by_type else None,
            "most_problematic_stage": max(self.errors_by_stage.items(), key=lambda x: x[1]) if self.errors_by_stage else None,
            "most_problematic_function": max(self.errors_by_function.items(), key=lambda x: x[1]) if self.errors_by_function else None,
        }

    def get_performance_insights(self) -> List[str]:
        """Get performance insights and recommendations."""
        insights = []

        if self.total_executions == 0:
            return ["No data available for analysis"]

        # Success rate analysis
        success_rate = self.successful_executions / self.total_executions
        if success_rate < 0.9:
            insights.append(f"Low success rate ({success_rate:.1%}). Consider reviewing error patterns and improving reliability.")
        elif success_rate > 0.99:
            insights.append(f"Excellent success rate ({success_rate:.1%}). System is performing well.")

        # Performance analysis
        avg_time = self.total_execution_time / self.total_executions
        if avg_time > 10.0:
            insights.append(f"High average execution time ({avg_time:.2f}s). Consider optimizing slow functions.")

        # Retry analysis
        avg_retries = self.total_retries / self.total_executions
        if avg_retries > 0.5:
            insights.append(f"High retry rate ({avg_retries:.2f} avg). Consider improving reliability or adjusting retry configuration.")

        # Stage timing analysis
        total_stage_time = self.perceive_time_total + self.operate_time_total + self.enforce_time_total
        if total_stage_time > 0:
            perceive_pct = (self.perceive_time_total / total_stage_time) * 100
            operate_pct = (self.operate_time_total / total_stage_time) * 100
            enforce_pct = (self.enforce_time_total / total_stage_time) * 100

            if perceive_pct > 30:
                insights.append(f"Perceive stage taking {perceive_pct:.1f}% of execution time. Consider optimizing input processing.")
            if operate_pct > 80:
                insights.append(f"Operate stage taking {operate_pct:.1f}% of execution time. This is expected for most functions.")
            if enforce_pct > 20:
                insights.append(f"Enforce stage taking {enforce_pct:.1f}% of execution time. Consider optimizing output validation.")

        # Error pattern analysis
        if self.errors_by_stage:
            most_error_stage = max(self.errors_by_stage.items(), key=lambda x: x[1])
            insights.append(f"Most errors occur in {most_error_stage[0]} stage ({most_error_stage[1]} errors). Focus optimization here.")

        return insights


class POEMetricsCollector(Loggable):
    """Advanced metrics collector for POE pipeline monitoring and analysis."""

    def __init__(self, storage_path: Optional[Path] = None, max_memory_entries: int = 1000, enable_persistence: bool = True):
        """
        Initialize metrics collector.

        Args:
            storage_path: Path for persistent storage (default: ~/.opendxa/poet/metrics/)
            max_memory_entries: Maximum entries to keep in memory
            enable_persistence: Whether to enable persistent storage
        """
        super().__init__()

        # Configure storage
        if storage_path is None:
            storage_path = Path.home() / ".opendxa" / "poet" / "metrics"

        self.storage_path = storage_path
        self.enable_persistence = enable_persistence
        self.max_memory_entries = max_memory_entries

        # In-memory storage for recent metrics
        self.recent_metrics: deque = deque(maxlen=max_memory_entries)

        # Aggregate statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        self.total_retries = 0

        # Function and domain tracking
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"executions": 0, "successes": 0, "failures": 0, "total_time": 0.0}
        )
        self.domain_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"executions": 0, "successes": 0, "failures": 0, "total_time": 0.0}
        )

        # Create storage directory
        if self.enable_persistence:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def record_execution(
        self,
        function_name: str,
        success: bool,
        total_time: float,
        attempts: int,
        domain: Optional[str] = None,
        stage_timings: Optional[Dict[str, float]] = None,
        error_info: Optional[Dict[str, str]] = None,
        config_info: Optional[Dict[str, Any]] = None,
    ) -> POEExecutionMetrics:
        """
        Record a POE execution with detailed metrics.

        Args:
            function_name: Name of the executed function
            success: Whether execution was successful
            total_time: Total execution time in seconds
            attempts: Number of attempts made
            domain: Domain plugin used (if any)
            stage_timings: Timing for each POE stage
            error_info: Error details (type, message, stage)
            config_info: Configuration used (retries, timeout, etc.)

        Returns:
            POEExecutionMetrics object
        """
        # Create metrics object
        metrics = POEExecutionMetrics(
            function_name=function_name, domain=domain, timestamp=time.time(), success=success, total_time=total_time, attempts=attempts
        )

        # Add stage timings
        if stage_timings:
            metrics.perceive_time = stage_timings.get("perceive", 0.0)
            metrics.operate_time = stage_timings.get("operate", 0.0)
            metrics.enforce_time = stage_timings.get("enforce", 0.0)
            metrics.train_time = stage_timings.get("train")

        # Add error information
        if error_info:
            metrics.error_type = error_info.get("type")
            metrics.error_message = error_info.get("message")
            metrics.error_stage = error_info.get("stage")

        # Add configuration information
        if config_info:
            metrics.retries_configured = config_info.get("retries", 3)
            metrics.timeout_configured = config_info.get("timeout", 30.0)
            metrics.training_enabled = config_info.get("training_enabled", False)

        # Update aggregates
        self._update_aggregates(metrics)

        # Store metrics
        self._store_metrics(metrics)

        return metrics

    def _update_aggregates(self, metrics: POEExecutionMetrics):
        """Update aggregate statistics."""
        self.total_executions += 1
        self.total_execution_time += metrics.total_time

        if metrics.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Track retries
        self.total_retries += metrics.attempts - 1

        # Update function stats
        func_stats = self.function_stats[metrics.function_name]
        func_stats["executions"] += 1
        func_stats["total_time"] += metrics.total_time

        if metrics.success:
            func_stats["successes"] += 1
        else:
            func_stats["failures"] += 1

        # Update domain stats
        if metrics.domain:
            domain_stats = self.domain_stats[metrics.domain]
            domain_stats["executions"] += 1
            domain_stats["total_time"] += metrics.total_time

            if metrics.success:
                domain_stats["successes"] += 1
            else:
                domain_stats["failures"] += 1

    def _store_metrics(self, metrics: POEExecutionMetrics):
        """Store metrics in memory and optionally persist to disk."""
        # Add to memory
        self.recent_metrics.append(metrics)

        # Persist to disk if enabled
        if self.enable_persistence:
            try:
                self._persist_metrics(metrics)
            except Exception as e:
                self.warning(f"Failed to persist metrics: {e}")

    def _persist_metrics(self, metrics: POEExecutionMetrics):
        """Persist metrics to disk storage."""
        # Create date-based filename
        date_str = datetime.fromtimestamp(metrics.timestamp).strftime("%Y-%m-%d")
        metrics_file = self.storage_path / f"poe_metrics_{date_str}.jsonl"

        # Append to JSONL file
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")

    def get_stats(self) -> Dict[str, Any]:
        """Get current aggregate statistics."""
        return {
            "total_executions": self.total_executions,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
            "failure_rate": self.failed_executions / max(self.total_executions, 1),
            "avg_execution_time": self.total_execution_time / max(self.total_executions, 1),
            "total_retries": self.total_retries,
            "avg_retries": self.total_retries / max(self.total_executions, 1),
        }

    def get_function_performance(self, function_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific function."""
        if function_name not in self.function_stats:
            return {"error": f"No metrics found for function '{function_name}'"}

        stats = self.function_stats[function_name]
        return {
            "function_name": function_name,
            "executions": stats["executions"],
            "success_rate": stats["successes"] / max(stats["executions"], 1),
            "avg_execution_time": stats["total_time"] / max(stats["executions"], 1),
            "total_time": stats["total_time"],
        }

    def get_domain_performance(self, domain: str) -> Dict[str, Any]:
        """Get performance metrics for a specific domain."""
        if domain not in self.domain_stats:
            return {"error": f"No metrics found for domain '{domain}'"}

        stats = self.domain_stats[domain]
        return {
            "domain": domain,
            "executions": stats["executions"],
            "success_rate": stats["successes"] / max(stats["executions"], 1),
            "avg_execution_time": stats["total_time"] / max(stats["executions"], 1),
            "total_time": stats["total_time"],
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_stats": self.get_stats(),
            "top_functions": dict(sorted(self.function_stats.items(), key=lambda x: x[1]["executions"], reverse=True)[:10]),
            "domain_breakdown": dict(self.domain_stats) if self.domain_stats else {},
            "recent_executions": len(self.recent_metrics),
        }

    def clear_metrics(self):
        """Clear all stored metrics."""
        self.recent_metrics.clear()
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        self.total_retries = 0
        self.function_stats.clear()
        self.domain_stats.clear()


# Global metrics collector instance
_global_collector: Optional[POEMetricsCollector] = None


def get_global_collector() -> POEMetricsCollector:
    """Get or create the global metrics collector."""
    global _global_collector
    if _global_collector is None:
        _global_collector = POEMetricsCollector()
    return _global_collector


def record_execution_metrics(function_name: str, success: bool, total_time: float, attempts: int, **kwargs) -> POEExecutionMetrics:
    """Convenience function to record execution metrics using the global collector."""
    return get_global_collector().record_execution(
        function_name=function_name, success=success, total_time=total_time, attempts=attempts, **kwargs
    )
