"""
Optimized conditional processing for Dana control flow.

This module provides high-performance conditional execution with
optimizations for boolean coercion and branch prediction.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import Conditional
from dana.core.lang.interpreter.executor.control_flow.exceptions import ReturnException
from dana.core.lang.sandbox_context import SandboxContext


class ConditionalHandler(Loggable):
    """Optimized conditional handler for Dana control flow.

    This handler manages:
    - If/elif/else statements with condition optimization
    - Boolean coercion with smart caching
    - Branch execution tracking
    - Nested conditional optimization

    Performance optimizations:
    - Boolean coercion result caching
    - Branch prediction statistics
    - Condition evaluation optimization
    - Memory-efficient execution patterns
    """

    # Configuration constants
    CONDITION_CACHE_SIZE = 200  # Max cached boolean conversions
    BRANCH_STATS_LIMIT = 1000  # Max branch statistics entries

    def __init__(self, parent_executor=None):
        """Initialize the conditional handler.

        Args:
            parent_executor: Reference to parent executor for statement execution
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._condition_cache: dict[tuple[type, Any], bool] = {}  # Cache for boolean coercion results
        self._branch_stats: dict[str, int] = {}  # Statistics for branch prediction
        self._conditionals_executed = 0  # Performance tracking

    def execute_conditional(self, node: Conditional, context: SandboxContext) -> Any:
        """Execute a conditional statement with optimized evaluation.

        Args:
            node: The conditional statement to execute
            context: The execution context

        Returns:
            The result of the last executed statement in the chosen branch

        Raises:
            ReturnException: If a return statement is encountered in any branch
        """
        # Check parent executor is available
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        # Evaluate the condition with caching
        condition_value = self.parent_executor.execute(node.condition, context)
        condition = self._coerce_to_bool_cached(condition_value)

        # Track conditional execution and branch statistics
        self._conditionals_executed += 1
        branch_key = self._get_branch_key(node, condition)
        self._update_branch_stats(branch_key)

        self.debug(f"Conditional evaluation: condition={condition}, branch={branch_key}")

        # Execute the appropriate branch
        try:
            if condition:
                result = self._execute_statement_list(node.body, context)
                self.debug("Executed if branch")
            elif node.else_body:
                result = self._execute_statement_list(node.else_body, context)
                self.debug("Executed else branch")
            else:
                result = None
                self.debug("No else branch, returning None")
        except ReturnException:
            # Re-raise ReturnException to propagate it up to the function level
            self.debug("ReturnException caught in conditional branch, re-raising")
            raise

        return result

    def _coerce_to_bool_cached(self, value: Any) -> bool:
        """Coerce a value to boolean with smart caching for performance.

        Args:
            value: The value to convert to boolean

        Returns:
            Boolean representation of the value
        """
        # Create cache key based on value type and content
        value_type = type(value)
        cache_key = (value_type, value) if self._is_cacheable_value(value) else None

        # Check cache first for cacheable values
        if cache_key is not None and cache_key in self._condition_cache:
            return self._condition_cache[cache_key]

        # Perform boolean coercion with smart logic
        try:
            from dana.core.lang.interpreter.unified_coercion import TypeCoercion

            # Use smart boolean coercion if available and enabled
            if TypeCoercion.should_enable_coercion():
                result = TypeCoercion.coerce_to_bool_smart(value)
            else:
                result = bool(value)

        except ImportError:
            # TypeCoercion not available, use standard truthiness
            result = bool(value)
        except Exception:
            # Any error in coercion, use standard truthiness
            result = bool(value)

        # Cache the result if cacheable and within size limit
        if cache_key is not None and len(self._condition_cache) < self.CONDITION_CACHE_SIZE:
            self._condition_cache[cache_key] = result

        return result

    def _get_branch_key(self, node: Conditional, condition: bool) -> str:
        """Generate a key for branch statistics tracking.

        Args:
            node: The conditional node
            condition: The evaluated condition

        Returns:
            A key identifying the branch taken
        """
        # Create a simple key based on condition result and presence of else
        if condition:
            return "if_branch"
        elif node.else_body:
            return "else_branch"
        else:
            return "no_else"

    def _update_branch_stats(self, branch_key: str) -> None:
        """Update branch prediction statistics.

        Args:
            branch_key: The branch key to update
        """
        # Simple branch counting with size limit
        if len(self._branch_stats) >= self.BRANCH_STATS_LIMIT:
            # Remove least frequent entry to make space
            if self._branch_stats:
                min_key = min(self._branch_stats.keys(), key=lambda k: self._branch_stats[k])
                del self._branch_stats[min_key]

        self._branch_stats[branch_key] = self._branch_stats.get(branch_key, 0) + 1

    def _is_cacheable_value(self, value: Any) -> bool:
        """Check if a value can be safely cached.

        Args:
            value: The value to check

        Returns:
            True if value is cacheable (immutable and hashable)
        """
        try:
            # Test if value is hashable (required for dict keys)
            hash(value)
            # Only cache simple immutable types to avoid memory issues
            return isinstance(value, int | float | str | bool | type(None) | tuple)
        except (TypeError, AttributeError):
            return False

    def _execute_statement_list(self, statements: list[Any], context: SandboxContext) -> Any:
        """Execute a list of statements with optimization.

        Args:
            statements: The statements to execute
            context: The execution context

        Returns:
            The result of the last statement executed

        Raises:
            ReturnException: If a return statement is encountered
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        result = None
        for statement in statements:
            try:
                result = self.parent_executor.execute(statement, context)
            except ReturnException:
                # Re-raise ReturnException to propagate it up to the function level
                raise
        return result

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._condition_cache.clear()
        self._branch_stats.clear()
        self._conditionals_executed = 0
        self.debug("Conditional handler cache cleared")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get conditional performance statistics."""
        total_branches = sum(self._branch_stats.values())

        return {
            "conditionals_executed": self._conditionals_executed,
            "total_branches_taken": total_branches,
            "condition_cache_size": len(self._condition_cache),
            "branch_statistics": dict(self._branch_stats),
            "condition_cache_limit": self.CONDITION_CACHE_SIZE,
            "branch_stats_limit": self.BRANCH_STATS_LIMIT,
        }
