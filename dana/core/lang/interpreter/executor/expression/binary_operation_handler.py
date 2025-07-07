"""
Optimized binary operation handler for Dana expressions.

This module provides high-performance binary operation processing with
optimizations for common arithmetic and logical operations.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import BinaryExpression, BinaryOperator
from dana.core.lang.sandbox_context import SandboxContext


class BinaryOperationHandler(Loggable):
    """Optimized binary operation handler for Dana expressions."""

    def __init__(self, parent_executor=None, pipe_executor=None):
        """Initialize the binary operation handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self.pipe_executor = pipe_executor
        self._operation_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def execute_binary_expression(self, node: BinaryExpression, context: SandboxContext) -> Any:
        """Execute a binary expression with optimized operation handling."""
        try:
            # Special handling for pipe operator
            if node.operator == BinaryOperator.PIPE:
                if self.pipe_executor:
                    return self.pipe_executor.execute_pipe(node.left, node.right, context)
                else:
                    # Fallback to parent executor's pipe handling
                    if self.parent_executor and hasattr(self.parent_executor, "_execute_pipe"):
                        return self.parent_executor._execute_pipe(node.left, node.right, context)
                    else:
                        raise SandboxError("Pipe operation not supported without pipe executor")

            # Evaluate operands
            if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                raise SandboxError("Parent executor not properly initialized")
            left_raw = self.parent_executor.parent.execute(node.left, context)
            right_raw = self.parent_executor.parent.execute(node.right, context)

            # Extract actual values if wrapped
            left = self._extract_value(left_raw)
            right = self._extract_value(right_raw)

            # Apply type coercion if enabled
            left, right = self._apply_binary_coercion(left, right, node.operator.value)

            # Perform the operation
            if node.operator == BinaryOperator.ADD:
                return left + right
            elif node.operator == BinaryOperator.SUBTRACT:
                return left - right
            elif node.operator == BinaryOperator.MULTIPLY:
                return left * right
            elif node.operator == BinaryOperator.DIVIDE:
                return left / right
            elif node.operator == BinaryOperator.MODULO:
                return left % right
            elif node.operator == BinaryOperator.POWER:
                return left**right
            elif node.operator == BinaryOperator.EQUALS:
                return left == right
            elif node.operator == BinaryOperator.NOT_EQUALS:
                return left != right
            elif node.operator == BinaryOperator.LESS_THAN:
                return left < right
            elif node.operator == BinaryOperator.GREATER_THAN:
                return left > right
            elif node.operator == BinaryOperator.LESS_EQUALS:
                return left <= right
            elif node.operator == BinaryOperator.GREATER_EQUALS:
                return left >= right
            elif node.operator == BinaryOperator.AND:
                return bool(left and right)
            elif node.operator == BinaryOperator.OR:
                return bool(left or right)
            elif node.operator == BinaryOperator.IN:
                return left in right
            elif node.operator == BinaryOperator.IS:
                return left is right
            elif node.operator == BinaryOperator.IS_NOT:
                return left is not right
            else:
                raise SandboxError(f"Unsupported binary operator: {node.operator}")
        except (TypeError, ValueError) as e:
            raise SandboxError(f"Error evaluating binary expression with operator '{node.operator}': {e}")

    def _apply_binary_coercion(self, left: Any, right: Any, operator: str) -> tuple:
        """Apply type coercion to binary operands if enabled."""
        try:
            from dana.core.lang.interpreter.unified_coercion import TypeCoercion

            # Only apply coercion if enabled
            if TypeCoercion.should_enable_coercion():
                return TypeCoercion.coerce_binary_operands(left, right, operator)

        except ImportError:
            # TypeCoercion not available, return original values
            pass
        except Exception:
            # Any error in coercion, return original values
            pass

        return left, right

    def _extract_value(self, raw_value: Any) -> Any:
        """Extract actual value from potentially wrapped expressions."""
        if self.parent_executor and hasattr(self.parent_executor, "parent") and hasattr(self.parent_executor.parent, "extract_value"):
            return self.parent_executor.parent.extract_value(raw_value)
        return raw_value

    def clear_cache(self) -> None:
        """Clear the operation cache."""
        self._operation_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_lookups": total_lookups,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._operation_cache),
        }
