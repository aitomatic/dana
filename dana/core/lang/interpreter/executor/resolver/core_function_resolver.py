"""
Core Function Resolver - Registry functions with highest priority.

This resolver handles functions from the function registry, which includes
all core Dana functions and built-in functions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import FunctionType, ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext

from .base_resolver import FunctionResolverInterface


class CoreFunctionResolver(FunctionResolverInterface):
    """
    Resolver for core functions from the function registry.

    This resolver has the highest priority (10) and handles all functions
    registered in the function registry, including built-in functions
    and core Dana functions.
    """

    def __init__(self, function_registry: Any = None):
        """Initialize the core function resolver.

        Args:
            function_registry: The function registry instance
        """
        super().__init__()
        self.function_registry = function_registry

    def get_priority(self) -> int:
        """Get resolver priority (highest priority).

        Returns:
            Priority level 10 (high priority)
        """
        return 10

    def can_resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this resolver can potentially resolve the function.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            True if function exists in the registry
        """
        if not self.function_registry:
            return False

        # Check if the function actually exists in the registry
        names_to_try = [name_info.original_name]

        # Also try the base function name without namespace
        if name_info.func_name != name_info.original_name:
            names_to_try.append(name_info.func_name)

        for name_to_try in names_to_try:
            try:
                # Use None to search across all namespaces
                if self.function_registry.has(name_to_try, None):
                    return True
            except Exception:
                continue

        return False

    def resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Attempt to resolve function from the registry.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction if found in registry, None otherwise
        """
        if not self.function_registry:
            return None

        # Try original name first (e.g., "core.print", "print")
        names_to_try = [name_info.original_name]

        # Only try the base function name if:
        # 1. It's different from the original name AND
        # 2. There's no explicit scoping to non-registry namespaces (local, private, public, system)
        if name_info.func_name != name_info.original_name and not (
            name_info.namespace and name_info.namespace in ["local", "private", "public", "system"]
        ):
            names_to_try.append(name_info.func_name)

        self.logger.debug(f"CoreFunctionResolver trying names: {names_to_try} (namespace: {name_info.namespace})")

        for name_to_try in names_to_try:
            try:
                # Use None to search across all namespaces
                if self.function_registry.has(name_to_try, None):
                    self.logger.debug(f"Found in registry: {name_to_try}")
                    return ResolvedFunction(
                        func=None,  # Registry functions don't expose the actual function object
                        func_type=FunctionType.REGISTRY,
                        source="registry",
                        metadata={
                            "resolved_name": name_to_try,
                            "original_name": name_info.original_name,
                            "registry_lookup": True,
                        },
                    )
            except Exception as e:
                self.logger.debug(f"Registry lookup failed for '{name_to_try}': {e}")
                continue

        self.logger.debug(f"Function '{name_info.original_name}' not found in registry")
        return None
