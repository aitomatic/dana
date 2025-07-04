"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Print function implementation for the Dana interpreter.

This module provides the print function, which handles printing in the Dana interpreter.
"""

from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.sandbox_context import SandboxContext


def print_function(
    context: SandboxContext,
    *args: Any,
    options: dict[str, Any] | None = None,
) -> None:
    """Execute the print function.

    Args:
        context: The sandbox context
        *args: Values to print
        options: Optional parameters for the function

    Returns:
        None
    """
    logger = DANA_LOGGER.getLogger("dana.print")

    # Process each argument
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
    print(message)
    # Try to write to the executor's output buffer if available
    # Get the interpreter from context
    interpreter = getattr(context, "_interpreter", None)
    if interpreter is not None and hasattr(interpreter, "_executor"):
        executor = interpreter._executor
        if hasattr(executor, "_output_buffer"):
            # Write to the executor's output buffer for proper capture
            executor._output_buffer.append(message)
            return

    # Fallback to standard print if no executor available
