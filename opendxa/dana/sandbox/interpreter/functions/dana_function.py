"""
DANA function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, List

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.interpreter.functions.base_function import BaseFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction(BaseFunction, Loggable):
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

    def __do_call__(self, the_context: SandboxContext, *the_args: Any, **the_kwargs: Any) -> Any:
        """Execute the function body with the provided context and local context.

        Args:
            the_context: The context to use for execution
            local_context: The local context to use for execution
            *the_args: Positional arguments, not used because they’re already in the local scope
            **the_kwargs: Keyword arguments, not used because they’re already in the local scope
        """
        from opendxa.dana.sandbox.interpreter.executor.statement_executor import ReturnStatementExit

        try:
            for statement in self.body:
                result = the_context.interpreter.execute_statement(statement)
                self.debug(f"statement: {statement}, result: {result}")
        except ReturnStatementExit as e:
            return e.value
