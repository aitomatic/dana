"""
Dana function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.executor.control_flow.exceptions import ReturnException
from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction
from dana.core.lang.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A Dana function that can be called with arguments."""

    def __init__(
        self,
        body: list[Any],
        parameters: list[str],
        context: SandboxContext | None = None,
        return_type: str | None = None,
        defaults: dict[str, Any] | None = None,
        name: str | None = None,
    ):
        """Initialize a Dana function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
            return_type: The function's return type annotation
            defaults: Default values for parameters
            name: The function name
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters
        self.return_type = return_type
        self.defaults = defaults or {}
        self.__name__ = name or "unknown"  # Add __name__ attribute for compatibility
        self.debug(
            f"Created DanaFunction with name={self.__name__}, parameters={parameters}, return_type={return_type}, defaults={self.defaults}"
        )

    def prepare_context(self, context: SandboxContext | Any, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a Dana function.

        For Dana functions:
        - Starts with the function's original module context (for access to module variables)
        - Creates a clean local scope for the function
        - Sets up interpreter if needed
        - Applies default values for parameters
        - Maps arguments to the local scope

        Args:
            context: The current execution context or a positional argument
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Prepared context
        """
        # If context is not a SandboxContext, assume it's a positional argument
        if not isinstance(context, SandboxContext):
            args = [context] + args
            context = self.context.copy() if self.context else SandboxContext()

        # Start with the function's original module context (for access to module's public/private variables)
        if self.context is not None:
            prepared_context = self.context.copy()
            # Copy interpreter from current execution context if the module context doesn't have one
            if not hasattr(prepared_context, "_interpreter") or prepared_context._interpreter is None:
                if hasattr(context, "_interpreter") and context._interpreter is not None:
                    prepared_context._interpreter = context._interpreter
        else:
            # Fallback to current context if no module context available
            prepared_context = context.copy()

        # Store original local scope so we can restore it later
        original_locals = prepared_context.get_scope("local").copy()
        prepared_context._original_locals = original_locals

        # Keep existing variables but prepare to add function parameters
        # Don't clear the local scope - preserve existing variables

        # First, apply default values for all parameters that have them
        for param_name in self.parameters:
            if param_name in self.defaults:
                prepared_context.set(param_name, self.defaults[param_name])

        # Map positional arguments to parameters in the local scope (can override defaults)
        for i, param_name in enumerate(self.parameters):
            if i < len(args):
                prepared_context.set(param_name, args[i])

        # Map keyword arguments to the local scope (can override defaults and positional args)
        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in self.parameters:
                prepared_context.set(kwarg_name, kwarg_value)

        return prepared_context

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """
        Restore the context after Dana function execution.

        Args:
            context: The current context
            original_context: The original context before execution
        """
        # Restore the original local scope
        if hasattr(context, "_original_locals"):
            context.set_scope("local", context._original_locals)
            delattr(context, "_original_locals")

    def execute(self, context: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute the function with the given arguments.

        Args:
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the function execution
        """
        self.debug("DanaFunction.execute called with:")
        self.debug(f"  context: {type(context)}")
        self.debug(f"  args: {args}")
        self.debug(f"  kwargs: {kwargs}")
        self.debug(f"  parameters: {self.parameters}")
        self.debug(f"  body: {self.body}")
        self.debug(f"  return_type: {self.return_type}")

        try:
            # Prepare the execution context using the existing method
            prepared_context = self.prepare_context(context, list(args), kwargs)

            # Execute each statement in the function body
            result = None
            for statement in self.body:
                try:
                    # Use _interpreter attribute (with underscore)
                    if hasattr(prepared_context, "_interpreter") and prepared_context._interpreter is not None:
                        # Execute the statement and capture its result
                        stmt_result = prepared_context._interpreter.execute_statement(statement, prepared_context)
                        # Update result with the statement's value if it's not None
                        if stmt_result is not None:
                            result = stmt_result
                        self.debug(f"statement: {statement}, result: {stmt_result}")
                    else:
                        raise RuntimeError("No interpreter available in context")
                except ReturnException as e:
                    # Return statement was encountered - return its value
                    return e.value
                except Exception as e:
                    self.error(f"Error executing statement: {e}")
                    raise

            # Restore the original context if needed
            if isinstance(context, SandboxContext):
                self.restore_context(prepared_context, context)

            # Return the last non-None result
            return result

        except Exception as e:
            self.error(f"Error executing Dana function: {e}")
            raise
