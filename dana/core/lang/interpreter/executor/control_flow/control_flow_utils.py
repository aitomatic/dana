"""
Utility functions for Dana control flow execution.

This module provides simple control flow statement execution
for break, continue, and return statements.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import BreakStatement, ContinueStatement, ReturnStatement
from dana.core.lang.interpreter.executor.control_flow.exceptions import BreakException, ContinueException, ReturnException
from dana.core.lang.sandbox_context import SandboxContext


class ControlFlowUtils(Loggable):
    """Utility class for simple control flow statements.

    This utility handles:
    - Break statements (raise BreakException)
    - Continue statements (raise ContinueException)
    - Return statements (evaluate and raise ReturnException)

    Performance optimizations:
    - Minimal overhead for simple statements
    - Direct exception raising without complex logic
    - Optimized return value evaluation
    """

    def __init__(self, parent_executor=None):
        """Initialize the control flow utilities.

        Args:
            parent_executor: Reference to parent executor for expression evaluation
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._statements_executed = 0  # Performance tracking

    def execute_break_statement(self, node: BreakStatement, context: SandboxContext) -> None:
        """Execute a break statement.

        Args:
            node: The break statement to execute
            context: The execution context

        Raises:
            BreakException: Always
        """
        self._statements_executed += 1
        self.debug("Executing break statement")
        raise BreakException()

    def execute_continue_statement(self, node: ContinueStatement, context: SandboxContext) -> None:
        """Execute a continue statement.

        Args:
            node: The continue statement to execute
            context: The execution context

        Raises:
            ContinueException: Always
        """
        self._statements_executed += 1
        self.debug("Executing continue statement")
        raise ContinueException()

    def execute_return_statement(self, node: ReturnStatement, context: SandboxContext) -> None:
        """Execute a return statement.

        Args:
            node: The return statement to execute
            context: The execution context

        Returns:
            Never returns normally, raises a ReturnException

        Raises:
            ReturnException: With the return value
        """
        self._statements_executed += 1

        if node.value is not None:
            if self.parent_executor is None:
                raise RuntimeError("Parent executor not available for return value evaluation")
            value = self.parent_executor.execute(node.value, context)
            self.debug(f"Executing return statement with value: {value}")
        else:
            value = None
            self.debug("Executing return statement with no value")

        raise ReturnException(value)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get control flow utility performance statistics."""
        return {
            "statements_executed": self._statements_executed,
        }
