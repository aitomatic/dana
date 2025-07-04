"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Log level function implementation for the Dana interpreter.

This module provides the log_level function, which handles setting log levels in the Dana interpreter.
"""

from typing import Any

from dana.core.lang.log_manager import LogLevel, SandboxLogger
from dana.core.lang.sandbox_context import SandboxContext


def log_level_function(
    context: SandboxContext,
    level: str,
    namespace: str = "dana",
    options: dict[str, Any] | None = None,
) -> None:
    """Execute the log_level function to set the logging level for a namespace.

    Args:
        context: The runtime context for variable resolution.
        level: The log level to set (debug, info, warn, error).
        namespace: The namespace to set the level for (default: "dana").
        options: Optional parameters for the function.

    Returns:
        None

    Raises:
        RuntimeError: If the function execution fails.
        ValueError: If an invalid log level is provided.
    """
    if options is None:
        options = {}

    # Allow level and namespace override from options for backward compatibility
    level = level or options.get("level", "info")
    namespace = namespace or options.get("namespace", "dana")

    # Validate the log level
    valid_levels = {"debug", "info", "warn", "error"}
    if level.lower() not in valid_levels:
        raise ValueError(f"Invalid log level '{level}'. Must be one of: {', '.join(valid_levels)}")

    # Convert to LogLevel enum and set the namespace log level
    try:
        log_level_enum = LogLevel[level.upper()]
        SandboxLogger.set_log_level(log_level_enum, namespace, context)
    except KeyError:
        raise ValueError(f"Invalid log level '{level}'. Must be one of: {', '.join(valid_levels)}")
