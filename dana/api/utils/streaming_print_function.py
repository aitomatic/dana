"""
Streaming Print Function Override

This module provides a way to override the Dana print function
to enable real-time log streaming during execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Union
from collections.abc import Callable, Awaitable
import asyncio

from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.sandbox_context import SandboxContext


class StreamingPrintManager:
    """Manager for streaming print function overrides."""

    _current_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None

    @classmethod
    def set_streamer(cls, streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]) -> None:
        """Set the current log streamer."""
        cls._current_streamer = streamer

    @classmethod
    def clear_streamer(cls) -> None:
        """Clear the current log streamer."""
        cls._current_streamer = None

    @classmethod
    def stream_message(cls, level: str, message: str) -> None:
        """Stream a message if streamer is available."""
        if cls._current_streamer:
            try:
                result = cls._current_streamer(level, message)
                # Handle async streaming
                if asyncio.iscoroutine(result):
                    # For now, we can't easily handle async in this context
                    # So we'll make the streamer synchronous
                    pass
            except Exception as e:
                print(f"Warning: Log streaming failed: {e}")


def streaming_print_function(
    context: SandboxContext,
    *args: Any,
    options: dict[str, Any] | None = None,
) -> None:
    """
    Enhanced print function that streams output in real-time.

    This function replaces the standard Dana print function to enable
    real-time log streaming while maintaining all original functionality.

    Args:
        context: The sandbox context
        *args: Values to print
        options: Optional parameters for the function

    Returns:
        None
    """
    logger = DANA_LOGGER.getLogger("dana.print")

    # Process each argument (copied from original print_function.py)
    processed_args = []
    for arg in args:
        # Handle FStringExpression specially
        if hasattr(arg, "__class__") and arg.__class__.__name__ == "FStringExpression":
            logger.debug(f"Evaluating FStringExpression: {arg}")
            # Use the interpreter to evaluate the f-string expression
            interpreter = None
            if hasattr(context, "get_interpreter") and callable(context.get_interpreter):
                interpreter = context.get_interpreter()

            if interpreter is not None:
                try:
                    # Evaluate the f-string using the interpreter
                    evaluated_arg = interpreter.evaluate_expression(arg, context)
                    logger.debug(f"Evaluated f-string result: {evaluated_arg}")
                    processed_args.append(evaluated_arg)
                    continue
                except Exception as e:
                    logger.error(f"Error evaluating f-string: {e}")
                    # Fall back to string representation
            else:
                logger.debug("No interpreter available to evaluate f-string")

            # If we can't evaluate it properly, just use its string representation
            processed_args.append(str(arg))
        else:
            # For regular arguments, just convert to string
            processed_args.append(str(arg))

    # Join the processed arguments with a space separator
    message = " ".join(processed_args)

    # STREAM IMMEDIATELY (this is the key addition)
    StreamingPrintManager.stream_message("info", message)

    # Continue with original print function behavior
    print(message)  # Regular stdout

    # Try to write to the executor's output buffer if available
    interpreter = getattr(context, "_interpreter", None)
    if interpreter is not None and hasattr(interpreter, "_executor"):
        executor = interpreter._executor
        if hasattr(executor, "_output_buffer"):
            # Write to the executor's output buffer for proper capture
            executor._output_buffer.append(message)
            return

    # Fallback to standard print if no executor available
