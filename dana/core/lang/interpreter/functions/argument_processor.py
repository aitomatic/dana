"""
Argument processing for function calls in Dana.

This module provides utilities for evaluating and binding arguments to functions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import Callable
from typing import Any

from dana.common.exceptions import SandboxError
from dana.core.lang.sandbox_context import SandboxContext


class ArgumentProcessor:
    """
    Processes arguments for function calls in Dana.

    Responsibilities:
    - Evaluate argument expressions to concrete values
    - Bind arguments to function parameters
    - Handle positional and keyword arguments
    - Validate argument counts and names
    - Inject context when appropriate
    """

    def __init__(self, evaluator):
        """
        Initialize the ArgumentProcessor.

        Args:
            evaluator: The expression evaluator to use for evaluating arguments
        """
        self.evaluator = evaluator

    def evaluate_args(self, args: list[Any], kwargs: dict[str, Any], context: SandboxContext | None) -> tuple[list[Any], dict[str, Any]]:
        """
        Evaluate function arguments to concrete values.

        Args:
            args: List of argument expressions
            kwargs: Dictionary of keyword argument expressions
            context: The context for evaluation (can be None)

        Returns:
            Tuple of (evaluated_positional_args, evaluated_keyword_args)
        """
        evaluated_args = []
        evaluated_kwargs = {}

        # Special handling for 'args' and 'kwargs' in keyword arguments
        # This is a compatibility layer for old-style function calls
        if "args" in kwargs and isinstance(kwargs["args"], list):
            # These are positional arguments passed in old style
            # Just use them directly as positional args and evaluate each one
            for arg in kwargs.pop("args"):
                evaluated_arg = self._safe_evaluate(arg, context)
                evaluated_args.append(evaluated_arg)

        # Handle remaining positional arguments
        for arg in args:
            evaluated_arg = self._safe_evaluate(arg, context)
            evaluated_args.append(evaluated_arg)

        # Special handling for 'kwargs' in keyword arguments
        if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            # These are keyword arguments passed in old style
            # Merge them into the regular kwargs and remove the 'kwargs' entry
            old_kwargs = kwargs.pop("kwargs")
            for key, value in old_kwargs.items():
                if key not in kwargs:  # Don't overwrite explicit kwargs
                    kwargs[key] = value

        # Evaluate keyword arguments
        for key, value in kwargs.items():
            evaluated_kwargs[key] = self._safe_evaluate(value, context)

        return evaluated_args, evaluated_kwargs

    def _safe_evaluate(self, value: Any, context: SandboxContext | None) -> Any:
        """Safely evaluate a value, handling Python primitives directly."""
        # If it's already a Python primitive, return it directly
        if isinstance(value, int | float | str | bool | list | dict | tuple | set) or value is None:
            return value

        # Otherwise, use the evaluator
        try:
            return self.evaluator.evaluate(value, context)
        except Exception:
            # If evaluation fails, return the original value
            # This is a fallback for compatibility with existing code
            return value

    def bind_parameters(
        self,
        args: list[Any],
        kwargs: dict[str, Any],
        parameters: list[str],
        defaults: dict[str, Any] | None = None,
        context: SandboxContext | None = None,
    ) -> dict[str, Any]:
        """
        Bind arguments to function parameters.

        Args:
            args: Positional arguments
            kwargs: Keyword arguments
            parameters: List of parameter names
            defaults: Optional dictionary of default values for parameters
            context: Optional context to inject for 'context' parameter

        Returns:
            Dictionary of bound parameters

        Raises:
            SandboxError: If argument binding fails
        """
        # Create a dict for the bound parameters
        bound_params: dict[str, Any] = {}

        # Apply defaults if provided
        if defaults:
            for param, default_value in defaults.items():
                if param in parameters:
                    bound_params[param] = default_value

        # Bind positional arguments
        if len(args) > len(parameters):
            raise SandboxError(f"Too many arguments: expected {len(parameters)}, got {len(args)}")

        for i, arg in enumerate(args):
            if i < len(parameters):
                param = parameters[i]
                bound_params[param] = arg
            else:
                # This should never happen due to the check above, but added for safety
                raise SandboxError(f"Positional argument index {i} out of range")

        # Bind keyword arguments - allow overriding defaults
        for name, value in kwargs.items():
            if name not in parameters:
                raise SandboxError(f"Unknown parameter: {name}")
            # Allow keyword args to override defaults and positional args
            bound_params[name] = value

        # Inject context if there's a 'context' parameter and it's not already bound
        if context is not None and "context" in parameters and "context" not in bound_params:
            bound_params["context"] = context

        # Check that all required parameters are bound
        # Required parameters are those without defaults
        required_params = []
        for p in parameters:
            if defaults is None or p not in defaults:
                required_params.append(p)

        unbound = set(required_params) - set(bound_params.keys())

        if unbound:
            raise SandboxError(f"Missing arguments for parameters: {', '.join(unbound)}")

        return bound_params

    def process_arguments(
        self, func: Callable, args: list[Any], kwargs: dict[str, Any], context: SandboxContext | None = None
    ) -> dict[str, Any]:
        """
        Complete argument processing pipeline: evaluate arguments and bind to parameters.

        Args:
            func: The function being called
            args: List of argument expressions
            kwargs: Dictionary of keyword arguments expressions
            context: The context for evaluation (can be None)

        Returns:
            Dictionary of processed arguments ready to pass to the function

        Raises:
            SandboxError: If argument processing fails
        """
        try:
            # Extract function parameters and defaults
            parameters = getattr(func, "parameters", [])
            defaults = getattr(func, "defaults", {})

            # Evaluate the arguments
            evaluated_args, evaluated_kwargs = self.evaluate_args(args, kwargs, context)

            # Bind to parameters with context injection
            bound_args = self.bind_parameters(evaluated_args, evaluated_kwargs, parameters, defaults, context)

            return bound_args
        except Exception as e:
            # Wrap any exceptions to provide context
            func_name = getattr(func, "__name__", str(func))
            if isinstance(e, SandboxError):
                raise SandboxError(f"Error processing arguments for '{func_name}': {str(e)}")
            else:
                raise SandboxError(f"Unexpected error processing arguments for '{func_name}': {str(e)}")
