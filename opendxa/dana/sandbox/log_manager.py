"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Log level management for DANA runtime.
"""

import logging
from enum import Enum
from typing import Optional, Union

from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class LogLevel(Enum):
    """Log level management for DANA runtime."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR


class LogManager:
    """Log level management for DANA runtime."""

    @staticmethod
    def set_system_log_level(level: Union[LogLevel, str], context: Optional[SandboxContext] = None) -> None:
        """Set the log level for DANA runtime.

        This is the single source of truth for setting log levels in DANA.
        All components should use this function to change log levels.

        Args:
            level: The log level to set, can be a LogLevel enum or a string
        """
        if isinstance(level, str):
            level = LogLevel[level]

        DXA_LOGGER.setLevel(level.value, scope="opendxa.dana")
        if context:
            context.set("system.__log_level", level)
