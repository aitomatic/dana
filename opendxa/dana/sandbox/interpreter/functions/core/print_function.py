"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Print function implementation for the DANA interpreter.

This module provides the print function, which handles printing in the DANA interpreter.
"""

from typing import Any, Dict, Optional

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def print_function(
    *args: Any,
    context: SandboxContext,
    options: Optional[Dict[str, Any]] = None,
) -> None:
    """Execute the print function.

    Args:
        *args: Values to print
        context: The sandbox context
        options: Optional parameters for the function

    Returns:
        None
    """
    logger = DXA_LOGGER.getLogger("opendxa.dana.print")

    # Process each argument
    processed_args = []
    for arg in args:
        # Handle FStringExpression specially
        if hasattr(arg, "__class__") and arg.__class__.__name__ == "FStringExpression":
            logger.debug(f"Evaluating FStringExpression: {arg}")
            # Use the interpreter to evaluate the f-string expression
            if hasattr(context, "get_interpreter") and callable(context.get_interpreter):
                interpreter = context.get_interpreter()
                try:
                    # Evaluate the f-string using the interpreter
                    evaluated_arg = interpreter.evaluate_expression(arg, context)
                    logger.debug(f"Evaluated f-string result: {evaluated_arg}")
                    processed_args.append(evaluated_arg)
                    continue
                except Exception as e:
                    logger.error(f"Error evaluating f-string: {e}")
                    # Fall back to string representation

            # If we can't evaluate it properly, just use its string representation
            processed_args.append(str(arg))
        else:
            # For regular arguments, just convert to string
            processed_args.append(str(arg))

    # Join the processed arguments with a space separator
    message = " ".join(processed_args)

    # Print the message
    print(message)
