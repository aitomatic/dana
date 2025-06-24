"""
Optimized pipe operation handler for Dana expressions.

This module provides high-performance pipe operation processing with
optimizations for function composition and data flow pipelines.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.common.exceptions import SandboxError, StateError
from opendxa.dana.sandbox.parser.ast import BinaryExpression, Identifier
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class ComposedFunction:
    """A function composed from two other functions using the pipe operator."""

    def __init__(self, left_func: Any, right_func: Any, context: SandboxContext, parent_executor: Any = None):
        """Initialize a composed function.

        Args:
            left_func: The left function in the composition
            right_func: The right function in the composition
            context: The execution context
            parent_executor: Reference to parent executor for identifier resolution
        """
        self.left_func = left_func
        self.right_func = right_func
        self.context = context
        self.parent_executor = parent_executor
        # Add the expected attribute for tests
        self._is_dana_composed_function = True

    def execute(self, context: SandboxContext, *args, **kwargs) -> Any:
        """Execute the composed function: right_func(context, left_func(context, *args))."""
        # First call the left function
        intermediate_result = self._call_function(self.left_func, context, *args, **kwargs)

        # Then call the right function with the intermediate result
        return self._call_function(self.right_func, context, intermediate_result)

    def __call__(self, *args, **kwargs) -> Any:
        """Make the ComposedFunction callable directly."""
        # Extract context from args if present, otherwise use stored context
        if args and hasattr(args[0], "_state"):
            # First argument is likely a SandboxContext
            context = args[0]
            remaining_args = args[1:]
        else:
            context = self.context
            remaining_args = args

        return self.execute(context, *remaining_args, **kwargs)

    def _call_function(self, func: Any, context: SandboxContext, *args, **kwargs) -> Any:
        """Call a function with proper context handling."""
        from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction

        # Handle unresolved identifiers (deferred resolution)
        if isinstance(func, Identifier):
            # Try to resolve the identifier at call time
            try:
                # Try function registry first
                if (
                    hasattr(self, "parent_executor")
                    and self.parent_executor
                    and hasattr(self.parent_executor, "parent")
                    and hasattr(self.parent_executor.parent, "_function_executor")
                    and hasattr(self.parent_executor.parent._function_executor, "function_registry")
                ):
                    registry = self.parent_executor.parent._function_executor.function_registry
                    if registry.has(func.name):
                        resolved_func, func_type, metadata = registry.resolve(func.name)
                        return self._call_function(resolved_func, context, *args, **kwargs)

                # Try context lookup
                try:
                    resolved_func = context.get(func.name)
                    if callable(resolved_func):
                        return self._call_function(resolved_func, context, *args, **kwargs)
                    else:
                        raise SandboxError(f"'{func.name}' is not callable")
                except (KeyError, AttributeError):
                    pass

                # If still not found, raise error
                raise SandboxError(f"Function '{func.name}' not found in registry or context")

            except Exception as e:
                if isinstance(e, SandboxError):
                    raise
                raise SandboxError(f"Error resolving function '{func.name}': {e}")

        # Handle SandboxFunction objects
        if isinstance(func, SandboxFunction):
            return func.execute(context, *args, **kwargs)

        # Handle direct callables
        elif callable(func):
            try:
                # Try calling with context first
                return func(context, *args, **kwargs)
            except TypeError:
                # If that fails, try without context
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    raise SandboxError(f"Error calling function {func}: {e}")
        else:
            raise SandboxError(f"Cannot call non-callable object: {type(func)}")

    def __str__(self) -> str:
        """String representation of the composed function."""
        return f"ComposedFunction({self.left_func} | {self.right_func})"

    def __repr__(self) -> str:
        """Detailed representation of the composed function."""
        return f"ComposedFunction(left={self.left_func}, right={self.right_func})"


class PipeOperationHandler(Loggable):
    """Optimized pipe operation handler for Dana expressions."""

    # Performance constants
    PIPELINE_TRACE_THRESHOLD = 10  # Number of pipe operations before enabling trace
    COMPOSITION_CACHE_SIZE = 100  # Maximum number of cached function compositions

    def __init__(self, parent_executor: Any = None):
        """Initialize the pipe operation handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self._composition_cache = {}
        self._pipeline_trace_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def execute_pipe(self, left: Any, right: Any, context: SandboxContext) -> Any:
        """Execute a pipe operation: left | right."""
        try:
            # First, evaluate the right side if it's a BinaryExpression to see what it actually is
            right_value = right
            if isinstance(right, BinaryExpression):
                if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                    raise SandboxError("Parent executor not properly initialized")
                right_value = self.parent_executor.parent.execute(right, context)

            # Check if right side (or its evaluated form) is function-like
            right_is_function_like = self._is_function_like(right, context) or (
                right_value != right and (callable(right_value) or isinstance(right_value, ComposedFunction))
            )

            # Check for potential function composition first (before strict error checking)
            # Case 1: Simple Function composition (identifier | identifier or function)
            if (
                isinstance(left, Identifier)
                and (self._is_function_like(left, context) or True)  # Allow any identifier for composition
                and (right_is_function_like or isinstance(right, Identifier))  # Allow any identifier for composition
            ):
                # Create composed function
                left_func = self._resolve_function(left, context)
                right_func = right_value if right_value != right else self._resolve_function(right, context)
                return self._create_composed_function(left_func, right_func, context)

            # Now apply strict checking for non-composition cases
            if not right_is_function_like:
                # If right side is not a function, provide specific error message
                if isinstance(right, Identifier):
                    # Check if it's in function registry first
                    if (
                        self.parent_executor
                        and hasattr(self.parent_executor, "parent")
                        and hasattr(self.parent_executor.parent, "_function_executor")
                        and hasattr(self.parent_executor.parent._function_executor, "function_registry")
                    ):
                        registry = self.parent_executor.parent._function_executor.function_registry
                        if not registry.has(right.name):
                            # Check if it exists in context but is not a function
                            try:
                                value = context.get(right.name)
                                if not callable(value):
                                    raise SandboxError(f"Function '{right.name}' not found in registry")
                            except (KeyError, AttributeError):
                                raise SandboxError(f"Function '{right.name}' not found in registry")

                left_desc = self._describe_operand(left, context)
                right_desc = self._describe_operand(right, context)
                raise SandboxError(f"Invalid pipe operation: right operand must be a function. " f"Got {left_desc} | {right_desc}")

            # Case 2: Check if left side evaluates to a function (for chained composition)
            # For expressions like (func1 | func2) | func3
            elif not isinstance(left, Identifier):
                # Evaluate the left side first
                if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                    raise SandboxError("Parent executor not properly initialized")
                left_value = self.parent_executor.parent.execute(left, context)

                # If the left side evaluates to a function, this is function composition
                if callable(left_value) or isinstance(left_value, ComposedFunction):
                    right_func = right_value if right_value != right else self._resolve_function(right, context)
                    return self._create_composed_function(left_value, right_func, context)

                # Otherwise, it's a data pipeline
                else:
                    self._trace_pipe_step(context, right, left_value)
                    right_func = right_value if right_value != right else self._resolve_function(right, context)
                    return self._call_function(right_func, context, left_value)

            # Case 3: Data pipeline (data | function) - identifier that's not a function or literal data
            else:
                # Evaluate the left side to get the data
                if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                    raise SandboxError("Parent executor not properly initialized")
                data = self.parent_executor.parent.execute(left, context)
                self._trace_pipe_step(context, right, data)

                # Get the right function and call it with the data
                right_func = right_value if right_value != right else self._resolve_function(right, context)
                return self._call_function(right_func, context, data)

        except Exception as e:
            if isinstance(e, SandboxError):
                raise
            raise SandboxError(f"Error in pipe operation: {e}")

    def _is_function_like(self, expr: Any, context: SandboxContext) -> bool:
        """Check if an expression represents a function."""
        try:
            # Check for ComposedFunction objects
            if isinstance(expr, ComposedFunction):
                return True

            # Check for identifier that refers to a function
            if isinstance(expr, Identifier):
                # First check if it's registered as a function
                if (
                    self.parent_executor
                    and hasattr(self.parent_executor, "parent")
                    and hasattr(self.parent_executor.parent, "_function_executor")
                    and hasattr(self.parent_executor.parent._function_executor, "function_registry")
                ):
                    registry = self.parent_executor.parent._function_executor.function_registry
                    if registry.has(expr.name):
                        return True

                # Then check if it's a callable in context
                try:
                    value = context.get(expr.name)
                    return callable(value)
                except (KeyError, AttributeError):
                    pass

                # Finally try identifier resolver
                try:
                    if self.parent_executor and hasattr(self.parent_executor, "identifier_resolver"):
                        resolved = self.parent_executor.identifier_resolver.resolve_identifier(expr, context)
                        return callable(resolved)
                except:
                    pass

                return False

            # BinaryExpressions should NOT be treated as function-like in pipe operations
            # They should be evaluated as data (e.g., 5 | double should evaluate to 10)
            # if isinstance(expr, BinaryExpression):
            #     return True

            # Check for direct callable
            if callable(expr):
                return True

            return False

        except Exception:
            return False

    def _resolve_function(self, func_expr: Any, context: SandboxContext) -> Any:
        """Resolve a function expression to a callable function."""
        # If it's a ComposedFunction, return it directly
        if isinstance(func_expr, ComposedFunction):
            return func_expr

        # If it's already a callable, return it
        if callable(func_expr):
            return func_expr

        # If it's an identifier, resolve it
        if isinstance(func_expr, Identifier):
            # First try function registry
            if (
                self.parent_executor
                and hasattr(self.parent_executor, "parent")
                and hasattr(self.parent_executor.parent, "_function_executor")
                and hasattr(self.parent_executor.parent._function_executor, "function_registry")
            ):
                registry = self.parent_executor.parent._function_executor.function_registry
                if registry.has(func_expr.name):
                    func, func_type, metadata = registry.resolve(func_expr.name)
                    return func

            # Then try identifier resolver
            if self.parent_executor and hasattr(self.parent_executor, "identifier_resolver"):
                try:
                    resolved = self.parent_executor.identifier_resolver.resolve_identifier(func_expr, context)
                    if resolved is not None:
                        return resolved
                except:
                    pass

            # Try context lookup
            try:
                resolved = context.get(func_expr.name)
                if resolved is not None:
                    return resolved
            except:
                pass

            # If nothing found, return the identifier itself for deferred resolution
            # This allows composition with non-existent functions that will fail only when called
            return func_expr

        # If it's a binary expression, evaluate it
        if isinstance(func_expr, BinaryExpression):
            if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                raise SandboxError("Parent executor not properly initialized")
            return self.parent_executor.parent.execute(func_expr, context)

        # Try to execute it as an expression
        try:
            if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                raise SandboxError("Parent executor not properly initialized")
            return self.parent_executor.parent.execute(func_expr, context)
        except Exception as e:
            raise SandboxError(f"Cannot resolve function expression: {func_expr}. Error: {e}")

    def _create_composed_function(self, left_func: Any, right_func: Any, context: SandboxContext) -> ComposedFunction:
        """Create a composed function from two function expressions."""
        # Generate cache key for function composition
        cache_key = f"{id(left_func)}_{id(right_func)}"

        # Check cache first
        if cache_key in self._composition_cache:
            self._cache_hits += 1
            self.debug("Using cached composed function")
            return self._composition_cache[cache_key]

        self._cache_misses += 1

        # Resolve both functions
        resolved_left = self._resolve_function(left_func, context)
        resolved_right = self._resolve_function(right_func, context)

        # Validate that both are callable or identifiers (for deferred resolution)
        if not (callable(resolved_left) or isinstance(resolved_left, Identifier)):
            raise SandboxError(f"Left function must be callable or identifier, got {type(resolved_left)}")
        if not (callable(resolved_right) or isinstance(resolved_right, Identifier)):
            raise SandboxError(f"Right function must be callable or identifier, got {type(resolved_right)}")

        # Create and cache the composed function
        composed = ComposedFunction(resolved_left, resolved_right, context, self.parent_executor)

        # Manage cache size
        if len(self._composition_cache) >= self.COMPOSITION_CACHE_SIZE:
            # Remove oldest entry (simple FIFO eviction)
            oldest_key = next(iter(self._composition_cache))
            del self._composition_cache[oldest_key]

        self._composition_cache[cache_key] = composed

        self.debug(f"Created new composed function: {type(resolved_left)} | {type(resolved_right)}")
        return composed

    def _call_function(self, func: Any, context: SandboxContext, *args, **kwargs) -> Any:
        """Call a function with proper context detection and optimization."""
        from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction

        # Handle SandboxFunction objects (including ComposedFunction)
        if isinstance(func, SandboxFunction):
            return func.execute(context, *args, **kwargs)

        # Handle ComposedFunction
        if isinstance(func, ComposedFunction):
            return func.execute(context, *args, **kwargs)

        # Handle identifiers - delegate to function executor for consistency
        if isinstance(func, Identifier):
            from opendxa.dana.sandbox.parser.ast import FunctionCall

            # Convert arguments to FunctionCall format
            function_call_args = {}
            for i, arg in enumerate(args):
                function_call_args[str(i)] = arg
            function_call_args.update(kwargs)

            # Create and execute FunctionCall
            function_call = FunctionCall(name=func.name, args=function_call_args)
            if (
                not self.parent_executor
                or not hasattr(self.parent_executor, "parent")
                or not hasattr(self.parent_executor.parent, "_function_executor")
            ):
                raise SandboxError("Function executor not available")
            return self.parent_executor.parent._function_executor.execute_function_call(function_call, context)

        # Handle binary expressions (nested compositions)
        elif isinstance(func, BinaryExpression):
            if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                raise SandboxError("Parent executor not properly initialized")
            evaluated_func = self.parent_executor.parent.execute(func, context)
            return self._call_function(evaluated_func, context, *args, **kwargs)

        # Handle direct callables
        elif callable(func):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise SandboxError(f"Error calling function {func}: {e}")

        else:
            raise SandboxError(f"Cannot call non-callable object: {type(func)}")

    def _trace_pipe_step(self, context: SandboxContext, func: Any, input_data: Any) -> None:
        """Trace pipeline steps for debugging when enabled."""
        self._pipeline_trace_count += 1

        if self._pipeline_trace_count >= self.PIPELINE_TRACE_THRESHOLD:
            try:
                func_name = getattr(func, "__name__", str(func))
                data_preview = str(input_data)[:50] + ("..." if len(str(input_data)) > 50 else "")
                self.debug(f"Pipeline step {self._pipeline_trace_count}: {func_name}({data_preview})")
            except Exception:
                # Don't let tracing errors affect execution
                pass

    def clear_cache(self) -> None:
        """Clear the composition cache."""
        self._composition_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._pipeline_trace_count = 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "composition_cache_hits": self._cache_hits,
            "composition_cache_misses": self._cache_misses,
            "total_composition_lookups": total_lookups,
            "composition_hit_rate_percent": round(hit_rate, 2),
            "composition_cache_size": len(self._composition_cache),
            "pipeline_trace_count": self._pipeline_trace_count,
        }

    def _describe_operand(self, operand: Any, context: SandboxContext) -> str:
        """Get a descriptive string for an operand for error messages."""
        try:
            # Try to evaluate and get actual type
            if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
                return f"{type(operand).__name__}"

            try:
                value = self.parent_executor.parent.execute(operand, context)
                return f"{type(value).__name__}({value})"
            except Exception:
                return f"{type(operand).__name__}(unresolved)"
        except Exception:
            return f"{type(operand).__name__}"
