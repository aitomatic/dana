"""
Composed function implementation for Dana language.

This module provides a ComposedFunction class that represents the composition of two or more
SandboxFunction objects, enabling function composition like `add_ten | double`.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext


class ComposedFunction(SandboxFunction):
    """A composed function that applies multiple SandboxFunctions in sequence.

    This class represents the composition of two functions: left_func | right_func
    When called, it applies left_func first, then applies right_func to the result.

    ComposedFunctions can be composed with other ComposedFunctions recursively,
    enabling complex function pipelines like: a | b | c | d
    """

    def __init__(self, left_func: SandboxFunction | str, right_func: SandboxFunction | str, context: SandboxContext | None = None):
        """Initialize a composed function.

        Args:
            left_func: The first function to apply (SandboxFunction or function name for lazy resolution)
            right_func: The second function to apply (SandboxFunction or function name for lazy resolution)
            context: Optional sandbox context
        """
        super().__init__(context)
        self.left_func = left_func
        self.right_func = right_func

        # Store function registry reference for lazy resolution
        self._function_registry = None
        if context:
            interpreter = getattr(context, "_interpreter", None)
            if interpreter and hasattr(interpreter, "function_registry"):
                self._function_registry = interpreter.function_registry

        # Mark this as a Dana composed function for identification
        self._is_dana_composed_function = True

    def prepare_context(self, context: SandboxContext, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for composed function execution.

        For composed functions, we just pass through the context since the individual
        functions will handle their own context preparation.

        Args:
            context: The original context
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The context (passed through)
        """
        return context

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """
        Restore context after composed function execution.

        For composed functions, no special restoration is needed since the individual
        functions handle their own context restoration.

        Args:
            context: The current context
            original_context: The original context before execution
        """
        pass

    def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
        """Execute the composed function by applying left_func then right_func.

        Args:
            context: The execution context
            *args: Positional arguments to pass to the first function
            **kwargs: Keyword arguments to pass to the first function

        Returns:
            The result of applying right_func to the result of left_func
        """
        # Resolve functions if they are strings (lazy resolution)
        left_resolved = self._resolve_function(self.left_func, context)
        right_resolved = self._resolve_function(self.right_func, context)

        # Apply the left function first
        intermediate_result = left_resolved.execute(context, *args, **kwargs)

        # Apply the right function to the intermediate result
        # The intermediate result becomes the argument to the right function
        return right_resolved.execute(context, intermediate_result)

    def _resolve_function(self, func: SandboxFunction | str, context: SandboxContext) -> SandboxFunction:
        """Resolve a function reference to a SandboxFunction object.

        Args:
            func: Either a SandboxFunction object or a function name string
            context: The execution context for function resolution

        Returns:
            A resolved SandboxFunction object

        Raises:
            SandboxError: If the function cannot be resolved
        """
        if isinstance(func, SandboxFunction):
            # Already resolved
            return func
        elif isinstance(func, str):
            # Need to resolve the function name
            # Try to get from context first
            try:
                func_obj = context.get(f"local:{func}")
                if isinstance(func_obj, SandboxFunction):
                    return func_obj
            except Exception:
                pass

            # Try to use the stored function registry
            if self._function_registry:
                try:
                    resolved_func, func_type, metadata = self._function_registry.resolve(func, None)
                    if isinstance(resolved_func, SandboxFunction):
                        return resolved_func
                except Exception:
                    pass

            # Try to get the interpreter's function registry from context as fallback
            interpreter = getattr(context, "_interpreter", None)
            if interpreter and hasattr(interpreter, "function_registry"):
                try:
                    resolved_func, func_type, metadata = interpreter.function_registry.resolve(func, None)
                    if isinstance(resolved_func, SandboxFunction):
                        return resolved_func
                except Exception:
                    pass

            # Function not found - raise a clear error
            raise SandboxError(f"Function '{func}' not found in context or function registry")
        else:
            raise SandboxError(f"Invalid function type: {type(func)}")

    def __repr__(self) -> str:
        """String representation of the composed function."""
        return f"ComposedFunction({self.left_func} | {self.right_func})"
