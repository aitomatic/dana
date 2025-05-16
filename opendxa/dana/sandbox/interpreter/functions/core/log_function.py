"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Log function implementation for the DANA interpreter.

This module provides the log function, which handles logging in the DANA interpreter.
"""

from typing import Any, Dict, Optional

from opendxa.dana.sandbox.sandbox_context import SandboxContext


def log_function(
    context: SandboxContext,
    options: Optional[Dict[str, Any]] = None,
) -> None:
    """Execute the log function.

    Args:
        context: The runtime context for variable resolution.
        options: Optional parameters for the function.

    Returns:
        None

    Raises:
        RuntimeError: If the function execution fails.
    """
    if options is None:
        options = {}

    message = options.get("message", "")
    level = options.get("level", "info")

    print(f"[{level.upper()}] {message}")
