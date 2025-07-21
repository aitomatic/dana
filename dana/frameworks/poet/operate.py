"""
POET Operate Phase - Core Enhancement Logic

This module implements the Operate (O) phase of the POET pipeline, responsible for:
1. Executing the main function logic
2. Invoking LLM/AI for enhancement (stub for now)
3. Domain-specific operation hooks
4. Logging and error handling

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time
from collections.abc import Callable
from typing import Any

from dana.common.utils.logging import DANA_LOGGER

from .core import POETConfig


class OperatePhase:
    """Operate phase implementation."""

    def __init__(self, config: POETConfig):
        self.config = config
        self.logger = DANA_LOGGER.getLogger(__name__)

    def operate(self, func: Callable, args: tuple[Any, ...], kwargs: dict[str, Any], context: dict[str, Any]) -> Any:
        """
        Execute the main function logic with retry support.

        Args:
            func: The function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            context: Execution context

        Returns:
            Function output
        """
        retries = self.config.retries
        last_error = None

        for attempt in range(retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < retries:
                    wait_time = 0.1 * (2**attempt)  # Exponential backoff
                    self.logger.warning(f"Retry {attempt + 1}/{retries} after error: {e}. Waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Function failed after {retries} retries: {e}")
                    raise last_error
