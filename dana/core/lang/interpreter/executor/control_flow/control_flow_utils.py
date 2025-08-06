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
        """Execute a return statement with intelligent Promise creation.

        Uses PromiseFactory to determine optimal execution strategy:
        - Nested contexts → synchronous execution (prevents deadlock)
        - Simple expressions → synchronous execution (avoids overhead)
        - Complex expressions → EagerPromise creation (enables concurrency)

        Args:
            node: The return statement to execute
            context: The execution context

        Returns:
            Never returns normally, raises a ReturnException

        Raises:
            ReturnException: With either direct value or Promise[T] based on strategy
        """
        self._statements_executed += 1

        if node.value is not None:
            if self.parent_executor is None:
                raise RuntimeError("Parent executor not available for return value evaluation")

            self.debug("Processing return statement with intelligent Promise creation")

            # Import the Promise factory
            from dana.core.concurrency.promise_factory import PromiseFactory

            # Create a computation function that will evaluate the return value
            captured_context = context.copy()
            captured_node_value = node.value

            def return_computation():
                self.debug("Return computation function called")
                try:
                    result = self.parent_executor.execute(captured_node_value, captured_context)  # type: ignore
                    self.debug(f"Return computation result: {result}")
                    return result
                except Exception as e:
                    self.debug(f"Return computation failed with error: {e}")
                    raise

            # Use PromiseFactory to create optimal execution strategy
            from dana.core.runtime import DanaThreadPool

            executor = DanaThreadPool.get_instance().get_executor()

            # The factory will decide: synchronous execution or EagerPromise creation
            promise_value = PromiseFactory.create_promise(
                return_computation,
                executor,
                node.value,  # type: ignore # Pass AST node for complexity analysis
            )

            self.debug(f"Promise factory returned: {type(promise_value)}")
        else:
            promise_value = None
            self.debug("Executing return statement with no value")

        raise ReturnException(promise_value)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get control flow utility performance statistics."""
        return {
            "statements_executed": self._statements_executed,
        }
