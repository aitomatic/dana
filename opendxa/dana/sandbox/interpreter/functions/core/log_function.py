"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Log function implementation for the Dana interpreter.

This module provides the log function, which handles logging in the Dana interpreter.
"""

from typing import Any, Dict, Optional

from opendxa.dana.sandbox.log_manager import SandboxLogger
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def log_function(
    context: SandboxContext,
    message: str,
    level: Optional[str] = "INFO",
    options: Optional[Dict[str, Any]] = None,
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

    SandboxLogger.log(message, level=level)  # type: ignore
