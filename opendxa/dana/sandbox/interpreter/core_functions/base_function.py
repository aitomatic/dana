"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Base function implementation for the DANA interpreter.

This module provides the BaseFunction class, which serves as the parent class
for all core DANA functions.
"""

from abc import ABC, abstractmethod
from typing import Any

from opendxa.dana.sandbox.sandbox_context import SandboxContext


class BaseFunction(ABC):
    """Base class for all DANA core functions.

    This class provides a common interface for all core functions.
    """

    @abstractmethod
    def call(
        self,
        context: SandboxContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute the function.

        Args:
            context: The runtime context for variable resolution.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function execution.

        Raises:
            RuntimeError: If the function execution fails.
        """
        pass
