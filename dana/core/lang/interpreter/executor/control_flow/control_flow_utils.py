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
        """Execute a return statement (lazy execution with Promise[T] creation).

        Args:
            node: The return statement to execute
            context: The execution context

        Returns:
            Never returns normally, raises a ReturnException with Promise[T] value

        Raises:
            ReturnException: With the Promise[T] value for lazy evaluation
        """
        self._statements_executed += 1

        if node.value is not None:
            if self.parent_executor is None:
                raise RuntimeError("Parent executor not available for return value evaluation")

            self.debug("About to create Promise for return statement")

            # Create a Promise[T] for eager evaluation (concurrent by default)
            from dana.core.concurrency import EagerPromise

            # Create a computation function that will evaluate the return value when accessed
            # Capture a copy of the current context to preserve function arguments and local variables
            # This prevents the context from being modified by restore_context later
            captured_context = context.copy()
            captured_node_value = node.value

            def return_computation():
                self.debug("Return computation function called")
                self.debug(f"Using captured context: {type(captured_context)}")
                # Debug: Check what's in the captured context
                try:
                    local_vars = captured_context.get_scope("local")
                    self.debug(f"Captured context local vars: {list(local_vars.keys())}")
                    # Check if Point struct is available
                    if "Point" in local_vars:
                        self.debug(f"Point struct found: {type(local_vars['Point'])}")
                    else:
                        self.debug("Point struct NOT found in captured context")
                    # Debug: Check function arguments
                    for key, value in local_vars.items():
                        if key in ["street", "city", "state", "zip_code", "country"]:
                            self.debug(f"Function arg {key}: {value}")
                except Exception as e:
                    self.debug(f"Error accessing captured context: {e}")
                try:
                    result = self.parent_executor.execute(captured_node_value, captured_context)
                    self.debug(f"Return computation result: {result}")
                    return result
                except Exception as e:
                    self.debug(f"Return computation failed with error: {e}")
                    raise

            # Create Promise[T] wrapper for eager evaluation (concurrent by default)
            self.debug("Calling EagerPromise.create...")
            self.debug(f"Return computation function: {return_computation}")
            promise_value = EagerPromise.create(return_computation, captured_context)
            self.debug(f"Promise created: {type(promise_value)}")
            self.debug(f"Executing return statement with Promise[T] value: {type(promise_value)}")
        else:
            promise_value = None
            self.debug("Executing return statement with no value")

        raise ReturnException(promise_value)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get control flow utility performance statistics."""
        return {
            "statements_executed": self._statements_executed,
        }
