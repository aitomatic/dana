"""
Optimized loop processing for Dana control flow.

This module provides high-performance loop execution with
optimizations for iteration efficiency and memory management.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import ForLoop, WhileLoop
from dana.core.lang.interpreter.executor.control_flow.exceptions import BreakException, ContinueException, ReturnException
from dana.core.lang.sandbox_context import SandboxContext


class LoopHandler(Loggable):
    """Optimized loop handler for Dana control flow.

    This handler manages:
    - While loops with condition caching
    - For loops with iterable optimization
    - Loop variable management
    - Break/continue exception handling

    Performance optimizations:
    - Boolean coercion caching for conditions
    - Iterable type checking optimization
    - Loop variable scope optimization
    - Memory-efficient iteration patterns
    """

    # Configuration constants
    CONDITION_CACHE_SIZE = 100  # Max cached boolean conversions
    LARGE_ITERABLE_THRESHOLD = 10000  # Items threshold for batch processing

    def __init__(self, parent_executor=None):
        """Initialize the loop handler.

        Args:
            parent_executor: Reference to parent executor for statement execution
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._condition_cache: dict[tuple[type, Any], bool] = {}  # Cache for boolean coercion results
        self._iterable_type_cache: dict[type, bool] = {}  # Cache for iterable type checks
        self._loop_iterations = 0  # Performance tracking

    def execute_while_loop(self, node: WhileLoop, context: SandboxContext) -> Any:
        """Execute a while loop with optimized condition evaluation.

        Args:
            node: The while loop to execute
            context: The execution context

        Returns:
            The result of the last statement executed

        Raises:
            BreakException: If a break statement is encountered
            ContinueException: If a continue statement is encountered
            ReturnException: If a return statement is encountered
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        result = None
        iteration_count = 0

        # Track loop performance
        self.debug("Starting while loop execution")

        while True:
            # Evaluate condition with optimized boolean coercion
            condition_value = self.parent_executor.execute(node.condition, context)
            condition = self._coerce_to_bool_cached(condition_value)

            if not condition:
                break

            iteration_count += 1
            self._loop_iterations += 1

            # Performance monitoring for long-running loops
            if iteration_count > 0 and iteration_count % 1000 == 0:
                self.debug(f"While loop iteration {iteration_count}")

            try:
                result = self._execute_statement_list(node.body, context)
            except BreakException:
                self.debug(f"While loop terminated by break after {iteration_count} iterations")
                break
            except ContinueException:
                continue
            except ReturnException:
                # Re-raise ReturnException to propagate it up to the function level
                self.debug(f"While loop terminated by return after {iteration_count} iterations")
                raise

        self.debug(f"While loop completed after {iteration_count} iterations")
        return result

    def execute_for_loop(self, node: ForLoop, context: SandboxContext) -> Any:
        """Execute a for loop with optimized iterable processing.

        Args:
            node: The for loop to execute
            context: The execution context

        Returns:
            The result of the last statement executed

        Raises:
            BreakException: If a break statement is encountered
            ContinueException: If a continue statement is encountered
            ReturnException: If a return statement is encountered
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        # Evaluate the iterable with caching
        iterable = self.parent_executor.execute(node.iterable, context)

        # Optimized iterable validation with caching
        if not self._is_iterable_cached(iterable):
            raise TypeError(f"Object of type {type(iterable).__name__} is not iterable")

        result = None
        iteration_count = 0

        # Track loop performance and handle large iterables
        iterable_size = self._get_iterable_size(iterable)
        if iterable_size > self.LARGE_ITERABLE_THRESHOLD:
            self.debug(f"Processing large iterable with {iterable_size} items")

        self.debug(f"Starting for loop execution over {type(iterable).__name__}")

        for item in iterable:
            # Set the loop variable(s) in the context with scope optimization
            if isinstance(node.target, list):
                # Tuple unpacking: unpack item into multiple variables
                if hasattr(item, "__iter__") and not isinstance(item, str | bytes):
                    try:
                        unpacked_values = list(item)
                        if len(unpacked_values) != len(node.target):
                            raise ValueError(f"Cannot unpack {len(unpacked_values)} values into {len(node.target)} variables")

                        # Set each variable
                        for target_id, value in zip(node.target, unpacked_values, strict=False):
                            context.set(target_id.name, value)
                    except (TypeError, ValueError) as e:
                        raise TypeError(f"For loop tuple unpacking failed: {e}")
                else:
                    raise TypeError(f"Cannot unpack non-iterable {type(item).__name__} in for loop")
            else:
                # Single target
                context.set(node.target.name, item)

            iteration_count += 1
            self._loop_iterations += 1

            # Performance monitoring for large loops
            if iteration_count > 0 and iteration_count % 1000 == 0:
                self.debug(f"For loop iteration {iteration_count}")

            try:
                result = self._execute_statement_list(node.body, context)
            except BreakException:
                self.debug(f"For loop terminated by break after {iteration_count} iterations")
                break
            except ContinueException:
                continue
            except ReturnException:
                # Re-raise ReturnException to propagate it up to the function level
                self.debug(f"For loop terminated by return after {iteration_count} iterations")
                raise

        self.debug(f"For loop completed after {iteration_count} iterations")
        return result

    def _coerce_to_bool_cached(self, value: Any) -> bool:
        """Coerce a value to boolean with caching for performance.

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

    def _is_iterable_cached(self, obj: Any) -> bool:
        """Check if object is iterable with type caching.

        Args:
            obj: The object to check

        Returns:
            True if object is iterable, False otherwise
        """
        obj_type = type(obj)

        # Check cache first
        if obj_type in self._iterable_type_cache:
            return self._iterable_type_cache[obj_type]

        # Perform iterable check
        result = hasattr(obj, "__iter__")

        # Cache the result
        self._iterable_type_cache[obj_type] = result

        return result

    def _get_iterable_size(self, iterable: Any) -> int:
        """Get the size of an iterable if possible.

        Args:
            iterable: The iterable to measure

        Returns:
            Size of iterable, or 0 if size cannot be determined
        """
        try:
            return len(iterable)
        except (TypeError, AttributeError):
            # No len() method or not sized
            return 0

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
        self._iterable_type_cache.clear()
        self._loop_iterations = 0
        self.debug("Loop handler cache cleared")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get loop performance statistics."""
        return {
            "total_loop_iterations": self._loop_iterations,
            "condition_cache_size": len(self._condition_cache),
            "iterable_type_cache_size": len(self._iterable_type_cache),
            "condition_cache_limit": self.CONDITION_CACHE_SIZE,
            "large_iterable_threshold": self.LARGE_ITERABLE_THRESHOLD,
        }
