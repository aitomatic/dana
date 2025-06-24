"""AST Traversal Optimization Package

This package provides performance optimizations for AST traversal in the Dana interpreter,
including result memoization, recursion safety, and execution monitoring.
"""

from opendxa.dana.sandbox.interpreter.executor.traversal.ast_execution_cache import ASTExecutionCache
from opendxa.dana.sandbox.interpreter.executor.traversal.optimized_traversal import OptimizedASTTraversal
from opendxa.dana.sandbox.interpreter.executor.traversal.performance_metrics import TraversalPerformanceMetrics
from opendxa.dana.sandbox.interpreter.executor.traversal.recursion_safety import (
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
