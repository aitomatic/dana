"""Optimized AST Traversal Engine"""

import time
from contextlib import contextmanager
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.executor.traversal.ast_execution_cache import ASTExecutionCache
from dana.core.lang.interpreter.executor.traversal.recursion_safety import (
    RecursionDepthMonitor,
)
from dana.core.lang.sandbox_context import SandboxContext


class OptimizedASTTraversal(Loggable):
    """High-performance AST traversal with caching and safety features."""

    def __init__(
        self, base_executor, enable_caching: bool = False, enable_recursion_safety: bool = True, enable_performance_tracking: bool = True
    ):
        """Initialize the optimized AST traversal engine.

        Args:
            base_executor: The base executor to delegate to
            enable_caching: Whether to enable execution result caching (TEMPORARILY DISABLED)
            enable_recursion_safety: Whether to enable recursion depth monitoring and circular reference detection
            enable_performance_tracking: Whether to track performance metrics
        """
        super().__init__()
        self.base_executor = base_executor

        # Configuration flags - caching disabled due to cache key generation issues
        self.enable_caching = False
        self.enable_recursion_safety = enable_recursion_safety
        self.enable_performance_tracking = enable_performance_tracking
        # Circular reference detection disabled - causes false positives with recursive functions
        self.enable_circular_detection = False

        # Initialize optimization components
        if self.enable_caching:
            from dana.core.lang.interpreter.executor.traversal.ast_execution_cache import ASTExecutionCache

            self.execution_cache = ASTExecutionCache()
        else:
            self.execution_cache = None

        if self.enable_recursion_safety:
            from dana.core.lang.interpreter.executor.traversal.recursion_safety import (
                CircularReferenceDetector,
                RecursionDepthMonitor,
            )

            self.recursion_monitor = RecursionDepthMonitor()
            # Only create circular detector if enabled (currently disabled due to false positives)
            if self.enable_circular_detection:
                self.circular_detector = CircularReferenceDetector()
            else:
                self.circular_detector = None
        else:
            self.recursion_monitor = None
            self.circular_detector = None

        if self.enable_performance_tracking:
            from dana.core.lang.interpreter.executor.traversal.performance_metrics import TraversalPerformanceMetrics

            self.performance_metrics = TraversalPerformanceMetrics()
        else:
            self.performance_metrics = None

        self.debug("Initialized OptimizedASTTraversal with caching and circular detection disabled")

    def execute_optimized(self, node: Any, context: SandboxContext) -> Any:
        """Execute node with full optimization stack."""
        node_type = type(node).__name__
        start_time = time.time()
        cache_hit = False

        try:
            # Phase 1: Safety checks (if enabled)
            if self.enable_recursion_safety and self.recursion_monitor:
                with self.recursion_monitor.track_execution(node_type):
                    # Only use circular detector if enabled and available
                    if self.enable_circular_detection and self.circular_detector:
                        with self.circular_detector.visit_node(node):
                            return self._execute_with_optimizations(node, context, node_type, start_time)
                    else:
                        return self._execute_with_optimizations(node, context, node_type, start_time)
            else:
                return self._execute_with_optimizations(node, context, node_type, start_time)

        except Exception:
            # Record failed execution in metrics
            execution_time = time.time() - start_time
            if self.enable_performance_tracking and self.performance_metrics:
                self.performance_metrics.record_execution(node_type, execution_time, cache_hit)
            raise

    def _execute_with_optimizations(self, node: Any, context: SandboxContext, node_type: str, start_time: float) -> Any:
        """Execute with caching and performance tracking."""
        cache_hit = False

        try:
            # Phase 2: Cache lookup (if enabled)
            if self.enable_caching and self.execution_cache:
                found, cached_result = self.execution_cache.get(node, context)
                if found:
                    cache_hit = True
                    execution_time = time.time() - start_time
                    if self.enable_performance_tracking and self.performance_metrics:
                        self.performance_metrics.record_execution(node_type, execution_time, cache_hit)
                    return cached_result

            # Phase 3: Execute using BaseExecutor's execute method to avoid infinite recursion
            # This bypasses the optimized execution to prevent calling ourselves again
            from dana.core.lang.interpreter.executor.base_executor import BaseExecutor

            result = BaseExecutor.execute(self.base_executor, node, context)

            # Phase 4: Cache result (if enabled and cacheable)
            if self.enable_caching and self.execution_cache:
                self.execution_cache.put(node, context, result)

            # Phase 5: Record performance metrics
            execution_time = time.time() - start_time
            if self.enable_performance_tracking and self.performance_metrics:
                self.performance_metrics.record_execution(node_type, execution_time, cache_hit)

            return result

        except Exception:
            # Record failed execution
            execution_time = time.time() - start_time
            if self.enable_performance_tracking and self.performance_metrics:
                self.performance_metrics.record_execution(node_type, execution_time, cache_hit)
            raise

    def invalidate_caches(self, context: SandboxContext) -> None:
        """Invalidate optimization caches when context changes."""
        if self.enable_caching and self.execution_cache:
            self.execution_cache.invalidate_context_dependent(context)

    def configure_optimization(
        self,
        enable_caching: bool | None = None,
        enable_recursion_safety: bool | None = None,
        enable_performance_tracking: bool | None = None,
        cache_size: int | None = None,
        max_recursion_depth: int | None = None,
    ) -> None:
        """Configure optimization settings."""
        if enable_caching is not None:
            self.enable_caching = enable_caching
            self.debug(f"Caching {'enabled' if enable_caching else 'disabled'}")

        if enable_recursion_safety is not None:
            self.enable_recursion_safety = enable_recursion_safety
            self.debug(f"Recursion safety {'enabled' if enable_recursion_safety else 'disabled'}")

        if enable_performance_tracking is not None:
            self.enable_performance_tracking = enable_performance_tracking
            self.debug(f"Performance tracking {'enabled' if enable_performance_tracking else 'disabled'}")

        if cache_size is not None:
            self.execution_cache = ASTExecutionCache(max_size=cache_size)
            self.debug(f"Cache size set to {cache_size}")

        if max_recursion_depth is not None:
            self.recursion_monitor = RecursionDepthMonitor(max_depth=max_recursion_depth, warning_threshold=int(max_recursion_depth * 0.8))
            self.debug(f"Max recursion depth set to {max_recursion_depth}")

    def get_optimization_statistics(self) -> dict[str, Any]:
        """Get comprehensive optimization statistics."""
        stats = {
            "optimization_enabled": {
                "caching": self.enable_caching,
                "recursion_safety": self.enable_recursion_safety,
                "performance_tracking": self.enable_performance_tracking,
            }
        }

        if self.enable_caching and self.execution_cache:
            stats["cache"] = self.execution_cache.get_statistics()

        if self.enable_recursion_safety and self.recursion_monitor:
            stats["recursion"] = self.recursion_monitor.get_statistics()

        if self.enable_performance_tracking and self.performance_metrics:
            stats["performance"] = self.performance_metrics.get_overall_statistics()

        return stats

    def log_optimization_report(self) -> None:
        """Log comprehensive optimization report."""
        self.info("=== AST Traversal Optimization Report ===")

        if self.enable_caching and self.execution_cache:
            self.execution_cache.log_statistics()

        if self.enable_recursion_safety and self.recursion_monitor:
            recursion_stats = self.recursion_monitor.get_statistics()
            self.info(
                f"Recursion: max depth {recursion_stats['max_depth_reached']}"
                f"/{recursion_stats['max_depth_limit']} "
                f"({recursion_stats['stack_depth_ratio']:.1%} of limit)"
            )

        if self.enable_performance_tracking and self.performance_metrics:
            self.performance_metrics.log_performance_report()

    def clear_all_caches(self) -> None:
        """Clear all optimization caches and reset statistics."""
        if self.enable_caching and self.execution_cache:
            self.execution_cache.clear()

        if self.enable_recursion_safety and self.recursion_monitor:
            self.recursion_monitor.reset_statistics()
        if self.enable_circular_detection and self.circular_detector:
            self.circular_detector.clear()

        if self.enable_performance_tracking and self.performance_metrics:
            self.performance_metrics.reset_metrics()

        self.info("Cleared all optimization caches and statistics")

    @contextmanager
    def performance_context(self, description: str = "execution"):
        """Context manager for performance tracking."""
        start_time = time.time()
        self.debug(f"Starting {description}")

        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.debug(f"Completed {description} in {elapsed:.3f}s")

    def is_healthy(self) -> bool:
        """Check if the optimization engine is in a healthy state."""
        try:
            # Check for reasonable cache hit rate (if we have enough data)
            if self.enable_caching and self.execution_cache:
                cache_stats = self.execution_cache.get_statistics()
                if cache_stats["total_requests"] > 100 and cache_stats["hit_rate"] < 0.1:
                    self.warning("Low cache hit rate detected")
                    return False

            # Check for excessive recursion depth
            if self.enable_recursion_safety and self.recursion_monitor:
                recursion_stats = self.recursion_monitor.get_statistics()
                if recursion_stats["stack_depth_ratio"] > 0.9:
                    self.warning("High recursion depth detected")
                    return False

            return True

        except Exception as e:
            self.error(f"Health check failed: {e}")
            return False
