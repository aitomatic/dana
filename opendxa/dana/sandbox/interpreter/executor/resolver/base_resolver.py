"""
Base resolver interface and common types for unified function dispatch.

This module defines the common interface that all function resolvers must implement,
as well as shared data structures for tracking resolution attempts.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext


class ResolutionStatus(Enum):
    """Status of a function resolution attempt."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    ERROR = "error"


@dataclass
class ResolutionAttempt:
    """Record of a function resolution attempt."""

    resolver_name: str
    name_info: FunctionNameInfo
    status: ResolutionStatus
    result: ResolvedFunction | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class FunctionResolverInterface(ABC):
    """Base interface for all function resolvers in the unified dispatch system."""

    def __init__(self):
        """Initialize the resolver."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_priority(self) -> int:
        """Get the priority of this resolver (lower numbers = higher priority).

        Returns:
            Priority level (0-100, where 0 is highest priority)
        """
        pass

    @abstractmethod
    def can_resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this resolver can potentially resolve the function.

        This is a fast check to determine if this resolver should be attempted.
        It should not perform expensive operations.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            True if this resolver might be able to resolve the function
        """
        pass

    @abstractmethod
    def resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Attempt to resolve the function.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction if found, None if not found

        Raises:
            Exception: If resolution fails due to an error (not just "not found")
        """
        pass

    def get_name(self) -> str:
        """Get the name of this resolver for logging and debugging.

        Returns:
            Human-readable name of the resolver
        """
        return self.__class__.__name__

    def create_attempt(
        self,
        name_info: FunctionNameInfo,
        status: ResolutionStatus,
        result: ResolvedFunction | None = None,
        error_message: str | None = None,
        **metadata,
    ) -> ResolutionAttempt:
        """Create a resolution attempt record.

        Args:
            name_info: Function name information
            status: Resolution status
            result: Resolved function if successful
            error_message: Error message if failed
            **metadata: Additional metadata

        Returns:
            ResolutionAttempt record
        """
        return ResolutionAttempt(
            resolver_name=self.get_name(),
            name_info=name_info,
            status=status,
            result=result,
            error_message=error_message,
            metadata=dict(metadata) if metadata else None,
        )
