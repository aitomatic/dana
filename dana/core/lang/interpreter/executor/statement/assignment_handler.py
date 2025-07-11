"""
Optimized assignment handler for Dana statements.

This module provides high-performance assignment processing with
optimizations for different assignment types and type coercion.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import Assignment, AttributeAccess, Identifier, SubscriptExpression
from dana.core.lang.sandbox_context import SandboxContext


class AssignmentHandler(Loggable):
    """Optimized assignment handler for Dana statements."""

    # Performance constants
    TYPE_COERCION_CACHE_SIZE = 200  # Cache for type coercion results
    ASSIGNMENT_TRACE_THRESHOLD = 100  # Number of assignments before tracing

    def __init__(self, parent_executor: Any = None):
        """Initialize the assignment handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self._type_mapping_cache = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
        }
        self._assignment_count = 0
        self._coercion_cache = {}

    def execute_assignment(self, node: Assignment, context: SandboxContext) -> Any:
        """Execute an assignment statement with optimized processing.

        Args:
            node: The assignment to execute
            context: The execution context

        Returns:
            The assigned value
        """
        self._assignment_count += 1

        try:
            # Handle type hints efficiently
            target_type = self._process_type_hint(node, context)

            # Evaluate the right side expression
            if not self.parent_executor or not hasattr(self.parent_executor, "parent") or self.parent_executor.parent is None:
                raise SandboxError("Parent executor not properly initialized")
            value = self.parent_executor.parent.execute(node.value, context)

            # Convert function lists to ParallelFunction for clean composition
            value = self._convert_function_list_to_parallel(value, context)

            # Apply type coercion if needed
            if target_type is not None:
                value = self._apply_type_coercion(value, target_type, node.target)

            # Execute the assignment based on target type
            self._execute_assignment_by_target(node.target, value, context)

            # Store the last value for implicit return
            context.set("system:__last_value", value)

            # Trace assignment if enabled
            self._trace_assignment(node.target, value)

            return value

        finally:
            # Clean up type information
            context.set("system:__current_assignment_type", None)

    def _process_type_hint(self, node: Assignment, context: SandboxContext) -> type | None:
        """Process type hint for assignment with caching.

        Args:
            node: The assignment node
            context: The execution context

        Returns:
            The target type if type hint is present, None otherwise
        """
        if not hasattr(node, "type_hint") or not node.type_hint:
            return None

        if not hasattr(node.type_hint, "name"):
            return None

        type_name = node.type_hint.name.lower()
        target_type = self._type_mapping_cache.get(type_name)

        if target_type:
            # Set the type information for IPV to access
            context.set("system:__current_assignment_type", target_type)

        return target_type

    def _apply_type_coercion(self, value: Any, target_type: type, target_node: Any) -> Any:
        """Apply type coercion with caching for performance.

        Args:
            value: The value to coerce
            target_type: The target type
            target_node: The assignment target node for error reporting

        Returns:
            The coerced value
        """
        # Create cache key based on value type and target type
        cache_key = (type(value).__name__, target_type.__name__, str(value)[:50])

        # Check cache first
        if cache_key in self._coercion_cache:
            cached_result, cached_exception = self._coercion_cache[cache_key]
            if cached_exception:
                raise cached_exception
            return cached_result

        try:
            from dana.core.lang.interpreter.unified_coercion import TypeCoercion

            coerced_value = TypeCoercion.coerce_value(value, target_type)

            # Cache successful coercion
            if len(self._coercion_cache) < self.TYPE_COERCION_CACHE_SIZE:
                self._coercion_cache[cache_key] = (coerced_value, None)

            return coerced_value

        except Exception as e:
            target_name = self._get_assignment_target_name(target_node)
            error = SandboxError(
                f"Assignment to '{target_name}' failed: cannot coerce value '{value}' to type '{target_type.__name__}': {e}"
            )

            # Cache the error to avoid repeated coercion attempts
            if len(self._coercion_cache) < self.TYPE_COERCION_CACHE_SIZE:
                self._coercion_cache[cache_key] = (None, error)

            raise error

    def _execute_assignment_by_target(self, target: Any, value: Any, context: SandboxContext) -> None:
        """Execute assignment based on target type with optimized dispatch.

        Args:
            target: The assignment target
            value: The value to assign
            context: The execution context
        """
        if isinstance(target, Identifier):
            # Simple variable assignment: x = value (most common case)
            context.set(target.name, value)

        elif isinstance(target, SubscriptExpression):
            # Subscript assignment: obj[key] = value or obj[slice] = value
            self._execute_subscript_assignment(target, value, context)

        elif isinstance(target, AttributeAccess):
            # Attribute assignment: obj.attr = value
            self._execute_attribute_assignment(target, value, context)

        else:
            target_type_name = type(target).__name__
            raise SandboxError(f"Unsupported assignment target type: {target_type_name}")

    def _execute_subscript_assignment(self, target: SubscriptExpression, value: Any, context: SandboxContext) -> None:
        """Execute a subscript assignment with optimization.

        Args:
            target: The subscript expression target
            value: The value to assign
            context: The execution context
        """
        from dana.core.lang.ast import SliceExpression, SliceTuple

        # Get the target object
        if not self.parent_executor or not hasattr(self.parent_executor, "parent") or self.parent_executor.parent is None:
            raise SandboxError("Parent executor not properly initialized")
        target_obj = self.parent_executor.parent.execute(target.object, context)

        # Handle different types of subscript assignments
        if isinstance(target.index, SliceExpression):
            # Single slice assignment: obj[start:stop] = value
            self._execute_slice_assignment(target_obj, target.index, value, context)

        elif isinstance(target.index, SliceTuple):
            # Multi-dimensional slice assignment: obj[slice1, slice2] = value
            self._execute_multidim_slice_assignment(target_obj, target.index, value, context)

        else:
            # Regular index assignment: obj[key] = value
            try:
                index = self.parent_executor.parent.execute(target.index, context)
                target_obj[index] = value
            except Exception as e:
                obj_name = self._get_assignment_target_name(target.object)
                raise SandboxError(f"Subscript assignment to {obj_name}[{target.index}] failed: {e}")

    def _execute_slice_assignment(self, target_obj: Any, slice_expr: Any, value: Any, context: SandboxContext) -> None:
        """Execute a slice assignment with optimization.

        Args:
            target_obj: The object to assign to
            slice_expr: The slice expression
            value: The value to assign
            context: The execution context
        """
        try:
            # Evaluate slice components
            start = self.parent_executor.parent.execute(slice_expr.start, context) if slice_expr.start else None
            stop = self.parent_executor.parent.execute(slice_expr.stop, context) if slice_expr.stop else None
            step = self.parent_executor.parent.execute(slice_expr.step, context) if slice_expr.step else None

            # Create slice object and assign
            slice_obj = slice(start, stop, step)
            target_obj[slice_obj] = value

        except Exception as e:
            raise SandboxError(f"Slice assignment failed: {e}")

    def _execute_multidim_slice_assignment(self, target_obj: Any, slice_tuple: Any, value: Any, context: SandboxContext) -> None:
        """Execute a multi-dimensional slice assignment.

        Args:
            target_obj: The object to assign to
            slice_tuple: The SliceTuple containing multiple slice expressions
            value: The value to assign
            context: The execution context
        """
        from dana.core.lang.ast import SliceExpression

        try:
            # Evaluate each slice in the tuple
            evaluated_slices = []
            for slice_item in slice_tuple.slices:
                if isinstance(slice_item, SliceExpression):
                    # Convert SliceExpression to Python slice object
                    start = self.parent_executor.parent.execute(slice_item.start, context) if slice_item.start else None
                    stop = self.parent_executor.parent.execute(slice_item.stop, context) if slice_item.stop else None
                    step = self.parent_executor.parent.execute(slice_item.step, context) if slice_item.step else None
                    slice_obj = slice(start, stop, step)
                    evaluated_slices.append(slice_obj)
                else:
                    # Regular index - evaluate the expression
                    index = self.parent_executor.parent.execute(slice_item, context)
                    evaluated_slices.append(index)

            # Create tuple of slices for multi-dimensional indexing and assign
            slice_tuple_obj = tuple(evaluated_slices)
            target_obj[slice_tuple_obj] = value

        except Exception as e:
            raise SandboxError(f"Multi-dimensional slice assignment failed: {e}")

    def _execute_attribute_assignment(self, target: AttributeAccess, value: Any, context: SandboxContext) -> None:
        """Execute an attribute assignment with optimization.

        Args:
            target: The attribute access target
            value: The value to assign
            context: The execution context
        """
        try:
            # Get the target object
            if not self.parent_executor or not hasattr(self.parent_executor, "parent") or self.parent_executor.parent is None:
                raise SandboxError("Parent executor not properly initialized")
            target_obj = self.parent_executor.parent.execute(target.object, context)

            # Set the attribute
            setattr(target_obj, target.attribute, value)

        except Exception as e:
            obj_name = self._get_assignment_target_name(target.object)
            raise SandboxError(f"Attribute assignment to {obj_name}.{target.attribute} failed: {e}")

    def _get_assignment_target_name(self, target: Any) -> str:
        """Get a string representation of the assignment target for error messages.

        Args:
            target: The assignment target

        Returns:
            String representation of the target
        """
        if isinstance(target, Identifier):
            return target.name
        elif isinstance(target, SubscriptExpression):
            obj_name = self._get_assignment_target_name(target.object)
            return f"{obj_name}[...]"
        elif isinstance(target, AttributeAccess):
            obj_name = self._get_assignment_target_name(target.object)
            return f"{obj_name}.{target.attribute}"
        else:
            return str(target)

    def _trace_assignment(self, target: Any, value: Any) -> None:
        """Trace assignment operations for debugging when enabled.

        Args:
            target: The assignment target
            value: The assigned value
        """
        if self._assignment_count >= self.ASSIGNMENT_TRACE_THRESHOLD:
            try:
                target_name = self._get_assignment_target_name(target)
                value_preview = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
                self.debug(f"Assignment #{self._assignment_count}: {target_name} = {value_preview}")
            except Exception:
                # Don't let tracing errors affect execution
                pass

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._coercion_cache.clear()
        self._assignment_count = 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        return {
            "coercion_cache_size": len(self._coercion_cache),
            "total_assignments": self._assignment_count,
            "cache_utilization_percent": round(len(self._coercion_cache) / max(self.TYPE_COERCION_CACHE_SIZE, 1) * 100, 2),
        }

    def _convert_function_list_to_parallel(self, value: Any, context: SandboxContext) -> Any:
        """Convert a list of functions to a ParallelFunction for clean composition.

        This enables standalone parallel composition like: pipeline = [f1, f2]

        Args:
            value: The value to potentially convert
            context: The execution context

        Returns:
            ParallelFunction if value is a list of functions, otherwise the original value
        """
        # Only convert if value is a list
        if not isinstance(value, list):
            return value

        # Check if all items in the list are callable (functions)
        if not value:  # Empty list
            return value

        for item in value:
            if not callable(item):
                # Contains non-callable items, don't convert
                return value

        # All items are callable, convert to ParallelFunction
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.executor.expression.pipe_operation_handler import ParallelFunction

        return ParallelFunction(value, context)
