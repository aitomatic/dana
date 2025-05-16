"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Base function implementation for the DANA interpreter.

This module provides the BaseFunction class, which serves as the parent class
for all core DANA functions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

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
        raise NotImplementedError("Function must implement call()")


class BaseFunctionRegistry:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
            instance._initialized = False
        return cls._instances[cls]

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._functions = {}
        self._initialized = True

    def register(self, name: str, func, metadata: Optional[Dict[str, Any]] = None):
        self._functions[name] = (func, metadata or {})

    def get(self, name):
        return self._functions[name][0]

    def has(self, name):
        return name in self._functions

    def list(self):
        return list(self._functions.keys())
