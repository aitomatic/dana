"""
DANA function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, List

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A DANA function that can be called with arguments."""

    def __init__(self, body: List[Any], parameters: List[str], context: SandboxContext):
        """Initialize a DANA function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters

    def __do_call__(self, context: SandboxContext, *the_args: Any, **the_kwargs: Any) -> Any:
        """Execute the function body with the provided context and local context.

        Args:
            context: The context to use for execution
            *the_args: Positional arguments
            **the_kwargs: Keyword arguments
        """
        from opendxa.dana.sandbox.interpreter.executor.statement_executor import ReturnStatementExit

        try:
            # If the context doesn't have an interpreter, assign the one from self.context
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                if self.context is not None and hasattr(self.context, "_interpreter") and self.context._interpreter is not None:
                    context._interpreter = self.context._interpreter

            # Copy args and kwargs into the local scope by parameter names, but only if they don't exist
            for i, param_name in enumerate(self.parameters):
                if i < len(the_args):
                    # Only set the parameter if it doesn't already exist in local scope
                    if not context.has(f"local.{param_name}"):
                        context.set_in_scope(param_name, the_args[i], scope="local")

            # Set any keyword args if they don't already exist
            for kwarg_name, kwarg_value in the_kwargs.items():
                if kwarg_name in self.parameters and not context.has(f"local.{kwarg_name}"):
                    context.set_in_scope(kwarg_name, kwarg_value, scope="local")

            for statement in self.body:
                result = context.interpreter.execute_statement(statement, context)
                self.debug(f"statement: {statement}, result: {result}")
        except ReturnStatementExit as e:
            return e.value
