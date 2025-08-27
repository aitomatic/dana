"""
Dana function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
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
        is_sync: bool = False,
    ):
        """Initialize a Dana function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
            return_type: The function's return type annotation
            defaults: Default values for parameters
            name: The function name
            is_sync: Whether this function should execute synchronously (no Promise wrapping)
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters
        self.return_type = return_type
        self.defaults = defaults or {}
        self.__name__ = name or "unknown"  # Add __name__ attribute for compatibility
        self.is_sync = is_sync  # NEW FIELD: indicates if function should execute synchronously
        self.debug(
            f"Created DanaFunction with name={self.__name__}, parameters={parameters}, return_type={return_type}, defaults={self.defaults}, is_sync={self.is_sync}"
        )

    def prepare_context(self, context: SandboxContext | Any, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a Dana function.

        This method creates a context that combines:
        1. The function's own context (for access to module functions)
        2. The current context (for access to current variables)
        3. Function parameters and arguments
        """
        # If the function has its own context, use it as the base
        if self.context is not None:
            # Create a child context from the function's context
            # This gives access to module functions and other context
            prepared_context = self.context.create_child_context()

            # Merge the current context's local scope into the prepared context
            # This allows the function to access current variables
            if isinstance(context, SandboxContext):
                for key, value in context.get_scope("local").items():
                    prepared_context.set(f"local:{key}", value)
        else:
            # Fallback to using the passed context if function has no context
            prepared_context = context

        # Store original local scope so we can restore it later
        original_locals = prepared_context.get_scope("local").copy()
        prepared_context._original_locals = original_locals

        # First, apply default values for all parameters that have them
        for param_name in self.parameters:
            if param_name in self.defaults:
                prepared_context.set_in_scope(param_name, self.defaults[param_name], scope="local")

        # Map positional arguments to parameters in the local scope (can override defaults)
        for i, param_name in enumerate(self.parameters):
            if i < len(args):
                prepared_context.set_in_scope(param_name, args[i], scope="local")

        # Map keyword arguments to the local scope (can override defaults and positional args)
        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in self.parameters:
                prepared_context.set_in_scope(kwarg_name, kwarg_value, scope="local")

        # Set the context variable to point to the prepared_context itself
        # This allows function code to access the execution context
        prepared_context.set_in_scope("context", prepared_context, scope="local")

        # Copy the interpreter from the original context to the prepared context
        if isinstance(context, SandboxContext) and hasattr(context, "_interpreter"):
            prepared_context._interpreter = context._interpreter

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

        # Store original context for restoration
        original_context = context if isinstance(context, SandboxContext) else None
        prepared_context = None

        try:
            # Prepare the execution context using the existing method
            prepared_context = self.prepare_context(context, list(args), kwargs)

            # Add function call to execution stack for debugging
            if hasattr(prepared_context, "error_context") and prepared_context.error_context:
                from dana.core.lang.interpreter.error_context import ExecutionLocation

                function_location = ExecutionLocation(function_name=self.__name__, filename=prepared_context.error_context.current_file)
                prepared_context.error_context.push_location(function_location)

            # Execute each statement in the function body
            result = None
            for i, statement in enumerate(self.body):
                try:
                    # Update current location for error reporting
                    if hasattr(prepared_context, "error_context") and prepared_context.error_context:
                        prepared_context.error_context.current_location = getattr(statement, "location", None)

                    # Use _interpreter attribute (with underscore)
                    if hasattr(prepared_context, "_interpreter") and prepared_context._interpreter is not None:
                        # Execute the statement and capture its result
                        stmt_result = prepared_context._interpreter._executor.execute(statement, prepared_context)
                        # Update result with the statement's value if it's not None
                        if stmt_result is not None:
                            result = stmt_result
                        self.debug(f"statement {i}: {statement}, result type: {type(stmt_result).__name__}")
                    else:
                        raise RuntimeError("No interpreter available in context")
                except ReturnException as e:
                    # Return statement was encountered - return its value
                    return e.value
                except Exception as e:
                    # Wrap in SandboxError with location information
                    error_msg = f"Error executing statement {i} in function '{self.__name__}': {e}"
                    if hasattr(prepared_context, "error_context") and prepared_context.error_context:
                        error_msg += f"\nLocation: {prepared_context.error_context.current_location}"
                    raise SandboxError(error_msg) from e

            # Return the last non-None result
            # Don't resolve Promises here - let the caller decide when to resolve
            return result

        except Exception as e:
            # Log the error with detailed context
            # self.error(f"Error executing Dana function '{self.__name__}': {e}", exc_info=True)

            # Add function context to error if possible
            if prepared_context and hasattr(prepared_context, "error_context") and prepared_context.error_context:
                error_context = prepared_context.error_context
                if hasattr(e, "add_context"):
                    e.add_context(f"Function: {self.__name__}", error_context.current_location)

            # Re-raise the exception
            raise

        finally:
            # Always restore the original context, even if an exception occurred
            if original_context and prepared_context:
                try:
                    self.restore_context(prepared_context, original_context)
                except Exception as restore_error:
                    self.error(f"Error restoring context after function execution: {restore_error}")

            # Pop function call from execution stack
            if prepared_context and hasattr(prepared_context, "error_context") and prepared_context.error_context:
                try:
                    prepared_context.error_context.pop_location()
                except Exception as stack_error:
                    self.error(f"Error popping function call from stack: {stack_error}")
