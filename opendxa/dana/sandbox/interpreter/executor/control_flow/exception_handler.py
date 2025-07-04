"""
Optimized exception handling for Dana control flow.

This module provides high-performance exception processing with
optimizations for try/catch/finally blocks and exception flow control.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.executor.control_flow.exceptions import ReturnException
from dana.core.lang.parser.ast import TryBlock
from dana.core.lang.sandbox_context import SandboxContext


class ExceptionHandler(Loggable):
    """Optimized exception handler for Dana control flow.

    This handler manages:
    - Try/except/finally block execution
    - Exception type matching and handling
    - Exception flow control and propagation
    - Performance tracking for exception paths

    Performance optimizations:
    - Exception type caching for matching
    - Exception flow tracing for debugging
    - Optimized exception propagation
    - Memory-efficient exception handling
    """

    # Configuration constants
    EXCEPTION_TYPE_CACHE_SIZE = 50  # Max cached exception type matches
    EXCEPTION_TRACE_LIMIT = 100  # Max exception traces to keep

    def __init__(self, parent_executor=None):
        """Initialize the exception handler.

        Args:
            parent_executor: Reference to parent executor for statement execution
        """
        super().__init__()
        self.parent_executor = parent_executor
        self._exception_type_cache: dict[type, bool] = {}  # Cache for exception type matching
        self._exception_traces: list[dict[str, Any]] = []  # Exception handling traces
        self._try_blocks_executed = 0  # Performance tracking

    def execute_try_block(self, node: TryBlock, context: SandboxContext) -> Any:
        """Execute a try/except/finally block with optimized exception handling.

        Args:
            node: The try block to execute
            context: The execution context

        Returns:
            The result of the last executed statement

        Raises:
            ReturnException: If a return statement is encountered and not caught
        """
        self.debug("Starting try block execution")
        self._try_blocks_executed += 1

        result = None
        exception_occurred = None
        exception_handled = False

        try:
            # Execute the try block with tracing
            self.debug("Executing try block body")
            result = self._execute_statement_list(node.body, context)
            self.debug(f"Try block completed successfully, result: {result}")

        except ReturnException:
            # ReturnException should propagate through try/catch, not be caught
            self.debug("ReturnException in try block, propagating")
            self._add_exception_trace("try_block", "ReturnException", "propagated")
            raise

        except Exception as e:
            # Store the exception for except block handling
            exception_occurred = e
            exception_type = type(e).__name__
            self.debug(f"Exception caught in try block: {exception_type}: {e}")
            self._add_exception_trace("try_block", exception_type, "caught")

            # Try to handle the exception with except blocks
            for i, except_block in enumerate(node.except_blocks):
                try:
                    # For now, catch all exceptions (exception_type filtering not implemented yet)
                    # TODO: Add proper exception type matching with caching
                    self.debug(f"Executing except block {i}")
                    result = self._execute_statement_list(except_block.body, context)
                    exception_handled = True
                    self._add_exception_trace("except_block", exception_type, "handled")
                    break

                except ReturnException:
                    # ReturnException from except block should propagate
                    self.debug("ReturnException in except block, propagating")
                    self._add_exception_trace("except_block", "ReturnException", "propagated")
                    raise

                except Exception as except_exception:
                    # If except block raises another exception, continue to next except block
                    except_type = type(except_exception).__name__
                    self.debug(f"Exception in except block {i}: {except_type}")
                    self._add_exception_trace("except_block", except_type, "failed")
                    continue

            # If no except block handled the exception, prepare to re-raise it
            if not exception_handled:
                self.debug("No except block handled exception, will re-raise after finally")
                self._add_exception_trace("exception_flow", exception_type, "unhandled")

        finally:
            # Execute finally block if present
            if node.finally_block:
                try:
                    self.debug("Executing finally block")
                    self._execute_statement_list(node.finally_block, context)
                    self.debug("Finally block completed successfully")
                    self._add_exception_trace("finally_block", "success", "completed")

                except ReturnException:
                    # ReturnException from finally block should propagate
                    self.debug("ReturnException in finally block, propagating")
                    self._add_exception_trace("finally_block", "ReturnException", "propagated")
                    raise

                except Exception as finally_exception:
                    # Exceptions in finally block are logged but don't override the result
                    finally_type = type(finally_exception).__name__
                    self.warning(f"Exception in finally block: {finally_type}: {finally_exception}")
                    self._add_exception_trace("finally_block", finally_type, "error")

        # Re-raise unhandled exception after finally block
        if exception_occurred is not None and not exception_handled:
            self.debug(f"Re-raising unhandled exception: {type(exception_occurred).__name__}")
            raise exception_occurred

        self.debug(f"Try block execution completed, returning: {result}")
        return result

    def _execute_statement_list(self, statements: list[Any], context: SandboxContext) -> Any:
        """Execute a list of statements with exception tracking.

        Args:
            statements: The statements to execute
            context: The execution context

        Returns:
            The result of the last statement executed

        Raises:
            ReturnException: If a return statement is encountered
        """
        if self.parent_executor is None:
            raise RuntimeError("Parent executor not available")

        result = None
        for statement in statements:
            try:
                result = self.parent_executor.execute(statement, context)
            except ReturnException:
                # Re-raise ReturnException to propagate it up to the function level
                raise
        return result

    def _add_exception_trace(self, block_type: str, exception_type: str, action: str) -> None:
        """Add an exception trace for debugging and performance analysis.

        Args:
            block_type: The type of block (try_block, except_block, finally_block, etc.)
            exception_type: The type of exception
            action: The action taken (caught, handled, propagated, etc.)
        """
        # Maintain trace size limit
        if len(self._exception_traces) >= self.EXCEPTION_TRACE_LIMIT:
            self._exception_traces.pop(0)  # Remove oldest trace

        trace_entry = {
            "block_type": block_type,
            "exception_type": exception_type,
            "action": action,
            "try_block_count": self._try_blocks_executed,
        }

        self._exception_traces.append(trace_entry)

    def clear_cache(self) -> None:
        """Clear all cached data and traces."""
        self._exception_type_cache.clear()
        self._exception_traces.clear()
        self._try_blocks_executed = 0
        self.debug("Exception handler cache cleared")

    def get_performance_stats(self) -> dict[str, Any]:
        """Get exception handling performance statistics."""
        # Analyze exception traces for statistics
        trace_stats: dict[str, int] = {}
        for trace in self._exception_traces:
            key = f"{trace['block_type']}_{trace['action']}"
            trace_stats[key] = trace_stats.get(key, 0) + 1

        return {
            "try_blocks_executed": self._try_blocks_executed,
            "exception_traces_count": len(self._exception_traces),
            "exception_type_cache_size": len(self._exception_type_cache),
            "trace_statistics": trace_stats,
            "exception_trace_limit": self.EXCEPTION_TRACE_LIMIT,
            "exception_type_cache_limit": self.EXCEPTION_TYPE_CACHE_SIZE,
        }

    def get_exception_traces(self) -> list[dict[str, Any]]:
        """Get recent exception traces for debugging.

        Returns:
            List of recent exception trace entries
        """
        return list(self._exception_traces)
