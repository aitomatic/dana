"""AST Traversal Optimization Package

This package provides performance optimizations for AST traversal in the Dana interpreter,
including result memoization, recursion safety, and execution monitoring.
"""

from dana.core.lang.interpreter.executor.traversal.ast_execution_cache import ASTExecutionCache
from dana.core.lang.interpreter.executor.traversal.optimized_traversal import OptimizedASTTraversal
from dana.core.lang.interpreter.executor.traversal.performance_metrics import TraversalPerformanceMetrics
from dana.core.lang.interpreter.executor.traversal.recursion_safety import (
    CircularReferenceDetector,
    RecursionDepthMonitor,
)

__all__ = [
    "ASTExecutionCache",
    "CircularReferenceDetector",
    "RecursionDepthMonitor",
    "OptimizedASTTraversal",
    "TraversalPerformanceMetrics",
]
