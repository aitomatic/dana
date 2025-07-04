"""Performance Metrics for AST Traversal"""

import time
from collections import defaultdict
from typing import Any

from dana.common.mixins.loggable import Loggable


class TraversalPerformanceMetrics(Loggable):
    """Collect and analyze AST traversal performance data."""

    def __init__(self):
        super().__init__()
        self.reset_metrics()

    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        self.execution_count_by_node_type: dict[str, int] = defaultdict(int)
        self.execution_time_by_node_type: dict[str, float] = defaultdict(float)
        self.cache_hit_count_by_node_type: dict[str, int] = defaultdict(int)
        self.cache_miss_count_by_node_type: dict[str, int] = defaultdict(int)
        self.total_execution_time = 0.0
        self.start_time = time.time()

    def record_execution(self, node_type: str, execution_time: float, cache_hit: bool) -> None:
        """Record an execution event."""
        self.execution_count_by_node_type[node_type] += 1
        self.execution_time_by_node_type[node_type] += execution_time
        self.total_execution_time += execution_time

        if cache_hit:
            self.cache_hit_count_by_node_type[node_type] += 1
        else:
            self.cache_miss_count_by_node_type[node_type] += 1

    def get_hot_node_types(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Get the most frequently executed node types."""
        return sorted(self.execution_count_by_node_type.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def get_slow_node_types(self, top_n: int = 10) -> list[tuple[str, float]]:
        """Get the node types with highest total execution time."""
        return sorted(self.execution_time_by_node_type.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def get_cache_efficiency_by_node_type(self) -> dict[str, dict[str, Any]]:
        """Get cache hit rates by node type."""
        efficiency = {}

        for node_type in self.execution_count_by_node_type:
            hits = self.cache_hit_count_by_node_type[node_type]
            misses = self.cache_miss_count_by_node_type[node_type]
            total = hits + misses

            efficiency[node_type] = {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate": hits / total if total > 0 else 0.0,
                "executions": self.execution_count_by_node_type[node_type],
                "avg_time": (
                    self.execution_time_by_node_type[node_type] / self.execution_count_by_node_type[node_type]
                    if self.execution_count_by_node_type[node_type] > 0
                    else 0.0
                ),
            }

        return efficiency

    def get_overall_statistics(self) -> dict[str, Any]:
        """Get comprehensive performance statistics."""
        total_hits = sum(self.cache_hit_count_by_node_type.values())
        total_misses = sum(self.cache_miss_count_by_node_type.values())
        total_cache_requests = total_hits + total_misses
        total_executions = sum(self.execution_count_by_node_type.values())

        elapsed_time = time.time() - self.start_time

        return {
            "total_executions": total_executions,
            "total_execution_time": self.total_execution_time,
            "elapsed_time": elapsed_time,
            "executions_per_second": total_executions / elapsed_time if elapsed_time > 0 else 0.0,
            "average_execution_time": (self.total_execution_time / total_executions if total_executions > 0 else 0.0),
            "cache_hit_rate": total_hits / total_cache_requests if total_cache_requests > 0 else 0.0,
            "cache_requests": total_cache_requests,
            "unique_node_types": len(self.execution_count_by_node_type),
            "performance_efficiency": (total_executions / self.total_execution_time if self.total_execution_time > 0 else 0.0),
        }

    def log_performance_report(self) -> None:
        """Log a comprehensive performance report."""
        stats = self.get_overall_statistics()
        hot_nodes = self.get_hot_node_types(5)
        slow_nodes = self.get_slow_node_types(5)

        self.info("=== AST Traversal Performance Report ===")
        self.info(
            f"Total: {stats['total_executions']} executions in {stats['elapsed_time']:.3f}s ({stats['executions_per_second']:.1f} exec/s)"
        )
        self.info(f"Cache: {stats['cache_hit_rate']:.1%} hit rate from {stats['cache_requests']} requests")
        self.info(f"Performance: {stats['performance_efficiency']:.1f} exec/ms average")

        if hot_nodes:
            self.info("Hot node types:")
            for node_type, count in hot_nodes:
                self.info(f"  {node_type}: {count} executions")

        if slow_nodes:
            self.info("Slow node types:")
            for node_type, total_time in slow_nodes:
                avg_time = total_time / self.execution_count_by_node_type[node_type]
                self.info(f"  {node_type}: {total_time:.3f}s total ({avg_time:.3f}s avg)")
