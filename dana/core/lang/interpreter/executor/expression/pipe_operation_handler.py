"""
Clean pipe operation handler for Dana function composition.

This module provides pure function composition using the pipe operator.
Supports the two-statement approach:
1. pipeline = f1 | f2 | [f3, f4]  (pure composition)
2. result = pipeline(data)        (pure application)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import BinaryExpression, BinaryOperator, Identifier, ListLiteral
from dana.core.lang.interpreter.functions.composed_function import ComposedFunction
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext


class ParallelFunction(SandboxFunction):
    """Function that executes multiple functions with the same input and returns a list of results.

    Note: Despite the name 'Parallel', this currently executes functions sequentially.
    The name reflects the conceptual parallel application of multiple functions to the same data.
    """

    def __init__(self, functions: list[Any], context: SandboxContext | None = None):
        """Initialize a parallel function.

        Args:
            functions: List of functions to execute with the same input
            context: The execution context (optional)
        """
        super().__init__()
        self.functions = functions
        self.context = context

    def execute(self, context: SandboxContext, *args, **kwargs) -> list[Any]:
        """Execute all functions with the same input and return list of results."""
        results = []

        # Execute each function with the same input (sequential execution)
        for func in self.functions:
            result = self._call_function(func, context, *args, **kwargs)
            results.append(result)

        return results

    def restore_context(self, context: SandboxContext) -> SandboxContext:
        """Restore context after function execution (required by SandboxFunction)."""
        # For parallel functions, we don't need special context restoration
        return context

    def _call_function(self, func: Any, context: SandboxContext, *args, **kwargs) -> Any:
        """Call a function with proper context handling."""
        # Handle SandboxFunction objects (including composed functions)
        if isinstance(func, SandboxFunction):
            return func.execute(context, *args, **kwargs)

        # Handle direct callables
        if callable(func):
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
        return f"ParallelFunction({self.functions})"

    def __repr__(self) -> str:
        return f"ParallelFunction(functions={self.functions})"


class PipeOperationHandler(Loggable):
    """Clean pipe operation handler for pure function composition."""

    def __init__(self, parent_executor: Any = None):
        """Initialize the pipe operation handler."""
        super().__init__()
        self.parent_executor = parent_executor

    def execute_pipe(self, left: Any, right: Any, context: SandboxContext) -> Any:
        """Execute a pipe operation for pure function composition.

        Supports only function-to-function composition:
        - f1 | f2 -> ComposedFunction
        - f1 | [f2, f3] -> Mixed composition
        - [f1, f2] | f3 -> Mixed composition

        Does NOT support data pipelines like: data | function
        """
        try:
            # Resolve left operand to a function
            left_func = self._resolve_to_function(left, context)

            # Handle different right operand types
            if isinstance(right, ListLiteral):
                # Right side is a list: f1 | [f2, f3]
                right_functions = []
                for item in right.items:
                    func = self._resolve_to_function(item, context)
                    right_functions.append(func)

                # Create parallel function from the list
                parallel_func = ParallelFunction(right_functions, context)

                # Create composed function using Dana's existing infrastructure
                return ComposedFunction(left_func, parallel_func, context=context)

            else:
                # Right side is a single function: f1 | f2
                right_func = self._resolve_to_function(right, context)

                # Create composed function using Dana's existing infrastructure
                return ComposedFunction(left_func, right_func, context=context)

        except Exception as e:
            if isinstance(e, SandboxError):
                raise
            raise SandboxError(f"Error in pipe composition: {e}")

    def _resolve_to_function(self, expr: Any, context: SandboxContext) -> Any:
        """Resolve an expression to a function.

        Handles:
        - Identifiers: resolve from context/registry
        - ListLiterals: create ParallelFunction
        - BinaryExpressions: evaluate recursively
        - Functions: return as-is
        """
        # Handle identifiers
        if isinstance(expr, Identifier):
            return self._resolve_identifier(expr, context)

        # Handle list literals (parallel functions)
        if isinstance(expr, ListLiteral):
            functions = []
            for item in expr.items:
                func = self._resolve_to_function(item, context)
                functions.append(func)
            return ParallelFunction(functions, context)

        # Handle binary expressions (nested compositions)
        if isinstance(expr, BinaryExpression) and expr.operator == BinaryOperator.PIPE:
            return self.execute_pipe(expr.left, expr.right, context)

        # Handle already composed functions and SandboxFunctions
        if isinstance(expr, (SandboxFunction, ParallelFunction)):
            return expr

        # Handle direct callables
        if callable(expr):
            return expr

        # Strict validation: reject non-callable objects early
        raise SandboxError(
            f"Cannot use non-function '{expr}' of type {type(expr).__name__} in pipe composition. Only functions are allowed."
        )

    def _resolve_identifier(self, identifier: Identifier, context: SandboxContext) -> Any:
        """Resolve an identifier to a function from context or registry."""
        resolved_value = None

        # Try context first
        try:
            resolved_value = context.get(identifier.name)
            if resolved_value is not None:
                # Validate that the resolved value is callable
                if not callable(resolved_value):
                    raise SandboxError(
                        f"Cannot use non-function '{identifier.name}' (value: {resolved_value}) of type {type(resolved_value).__name__} in pipe composition. Only functions are allowed."
                    )
                return resolved_value
        except (KeyError, AttributeError):
            pass

        # Try function registry if available
        if (
            self.parent_executor
            and hasattr(self.parent_executor, "parent")
            and hasattr(self.parent_executor.parent, "_function_executor")
            and hasattr(self.parent_executor.parent._function_executor, "function_registry")
        ):
            registry = self.parent_executor.parent._function_executor.function_registry
            if registry.has(identifier.name):
                resolved_func, func_type, metadata = registry.resolve(identifier.name)
                # Registry should only contain callable functions, but validate to be safe
                if not callable(resolved_func):
                    raise SandboxError(f"Registry contains non-callable for '{identifier.name}': {type(resolved_func).__name__}")
                return resolved_func

        # If not found, raise error
        raise SandboxError(f"Function '{identifier.name}' not found")
