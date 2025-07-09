"""
Optimized statement utilities handler for Dana statements.

This module provides high-performance processing for assert, pass, and raise
statements with optimizations for common patterns and error handling.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import SandboxError
from dana.common.mixins.loggable import Loggable
from dana.core.lang.ast import AssertStatement, PassStatement, RaiseStatement
from dana.core.lang.sandbox_context import SandboxContext


class StatementUtils(Loggable):
    """Optimized statement utilities handler for Dana statements."""

    # Performance constants
    ASSERTION_TRACE_THRESHOLD = 100  # Number of assertions before tracing

    def __init__(self, parent_executor: Any = None):
        """Initialize the statement utilities handler."""
        super().__init__()
        self.parent_executor = parent_executor
        self._assertion_count = 0

    def execute_assert_statement(self, node: AssertStatement, context: SandboxContext) -> None:
        """Execute an assert statement with optimized processing.

        Args:
            node: The assert statement to execute
            context: The execution context

        Returns:
            None if assertion passes

        Raises:
            AssertionError: If assertion fails
        """
        self._assertion_count += 1

        # Evaluate the condition
        if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
            raise SandboxError("Parent executor not properly initialized")
        condition = self.parent_executor.parent.execute(node.condition, context)

        # Fast path for successful assertions (most common case)
        if condition:
            self._trace_assertion("pass", str(node.condition)[:50])
            return None

        # Handle assertion failure
        message = "Assertion failed"
        if node.message is not None:
            try:
                message = str(self.parent_executor.parent.execute(node.message, context))
            except Exception as e:
                # If message evaluation fails, use a default message
                message = f"Assertion failed (message evaluation error: {e})"

        self._trace_assertion("fail", message[:100])
        raise AssertionError(message)

    def execute_pass_statement(self, node: PassStatement, context: SandboxContext) -> None:
        """Execute a pass statement with optimized processing.

        Args:
            node: The pass statement to execute
            context: The execution context

        Returns:
            None
        """
        # Pass statements do nothing by design - this is the most optimized implementation
        return None

    def execute_raise_statement(self, node: RaiseStatement, context: SandboxContext) -> None:
        """Execute a raise statement with optimized processing.

        Args:
            node: The raise statement to execute
            context: The execution context

        Returns:
            Never returns normally, raises an exception

        Raises:
            Exception: The raised exception
        """
        # Handle re-raise case (raise without value)
        if node.value is None:
            raise RuntimeError("No exception to re-raise")

        # Evaluate the exception value
        if not self.parent_executor or not hasattr(self.parent_executor, "parent"):
            raise SandboxError("Parent executor not properly initialized")
        value = self.parent_executor.parent.execute(node.value, context)

        # Evaluate from_value if present (chained exception)
        from_exception = None
        if node.from_value is not None:
            try:
                from_exception = self.parent_executor.parent.execute(node.from_value, context)
            except Exception as e:
                # If from_value evaluation fails, log warning but continue with main exception
                self.warning(f"Failed to evaluate exception chain 'from' value: {e}")

        # Raise the exception with proper chaining
        if isinstance(value, Exception):
            if from_exception is not None:
                raise value from from_exception
            else:
                raise value
        else:
            # Convert non-exception values to string and raise as runtime error
            error_message = str(value) if value is not None else "Unknown error"
            if from_exception is not None:
                raise RuntimeError(error_message) from from_exception
            else:
                raise RuntimeError(error_message)

    def _trace_assertion(self, result: str, info: str) -> None:
        """Trace assertion operations for debugging when enabled.

        Args:
            result: The assertion result ('pass' or 'fail')
            info: Additional information about the assertion
        """
        if self._assertion_count >= self.ASSERTION_TRACE_THRESHOLD:
            try:
                self.debug(f"Assertion #{self._assertion_count}: {result} - {info}")
            except Exception:
                # Don't let tracing errors affect execution
                pass

    def get_stats(self) -> dict[str, Any]:
        """Get statement utilities statistics."""
        return {
            "total_assertions": self._assertion_count,
        }
