"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Log function implementation for the Dana interpreter.

This module provides the log function, which handles logging in the Dana interpreter.
"""

from typing import Any

from dana.core.lang.log_manager import SandboxLogger
from dana.core.lang.sandbox_context import SandboxContext


def log_function(
    context: SandboxContext,
    message: str,
    level: str | None = "INFO",
    options: dict[str, Any] | None = None,
) -> None:
    """Execute the log function.

    Args:
        context: The runtime context for variable resolution.
        message: The message to log.
        level: Optional level of the log.
        options: Optional parameters for the function.

    Returns:
        None

    Raises:
        RuntimeError: If the function execution fails.
    """
    if options is None:
        options = {}

    message = message or options.get("message", "")
    level = level or options.get("level", "INFO")

    # Use "dana" namespace for user log calls - clean output
    SandboxLogger.log(message, level=str(level), context=context, namespace="dana")
