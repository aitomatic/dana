"""
Function resolution utilities for Dana language function execution.

This module provides utilities for resolving functions in the Dana language interpreter,
including namespace resolution and function lookup logic.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.executor.function_name_utils import FunctionNameInfo
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class ResolvedFunction:
    """Information about a resolved function."""

    def __init__(self, func: Any, func_type: str, source: str, metadata: dict[str, Any] | None = None):
        """Initialize resolved function information.

        Args:
            func: The resolved function object
            func_type: Type of function ('dana', 'python', 'builtin')
            source: Source of the function (e.g., 'core', 'local', 'registry')
            metadata: Optional metadata about the function
        """
        self.func = func
        self.func_type = func_type
        self.source = source
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation of resolved function."""
        return f"ResolvedFunction(type='{self.func_type}', source='{self.source}')"


class FunctionResolver:
    """Handles function resolution and namespace lookup."""

    def __init__(self, executor):
        """Initialize function resolver.

        Args:
            executor: The function executor instance
        """
        self.executor = executor
        self.logger = logging.getLogger(__name__)

    def parse_function_name(self, func_name: str) -> FunctionNameInfo:
        """Parse a function name and determine its namespace.

        Args:
            func_name: Function name to parse (e.g., 'func', 'core.print', 'local.my_func')

        Returns:
            FunctionNameInfo with parsed components
        """
        original_name = func_name

        if "." in func_name:
            # Handle namespaced function calls
            parts = func_name.split(".", 1)
            namespace = parts[0]
            func_name = parts[1]
            full_key = f"{namespace}.{func_name}"
        else:
            # Default to local namespace for unqualified names
            namespace = "local"
            full_key = f"local.{func_name}"

        return FunctionNameInfo(
            original_name=original_name,
            func_name=func_name,
            namespace=namespace,
            full_key=full_key
        )

    def resolve_function(self, name_info: FunctionNameInfo, context: SandboxContext, registry: Any) -> ResolvedFunction | None:
        """Resolve a function using the parsed name information.

        Args:
            name_info: Parsed function name information
            context: The execution context
            registry: The function registry

        Returns:
            ResolvedFunction with the resolved function and metadata, or None if not found

        Raises:
            FunctionRegistryError: If function cannot be resolved
        """
        # Try fully-scoped context first (local, private, public, etc.)
        func = self._resolve_from_context(name_info, context)
        if func:
            return func

        # Try registry second
        registry_func = self._resolve_from_registry(name_info, registry)
        if registry_func:
            return registry_func

        return None

    def _resolve_from_context(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Resolve function from all scoped context.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            Resolved function from all scoped context, or None if not found
        """
        try:
            func_data = context.get(name_info.full_key)
        except Exception:
            return None

        if func_data is None:
            return None

        # Determine function type and create resolved function
        from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
        from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction

        if isinstance(func_data, DanaFunction):
            # Dana functions are a type of sandbox function but need special handling
            return ResolvedFunction(func_data, "sandbox", "scoped_context")
        elif isinstance(func_data, SandboxFunction):
            return ResolvedFunction(func_data, "sandbox", "scoped_context")
        elif isinstance(func_data, dict) and func_data.get("type") == "function":
            # Legacy function dict format
            return ResolvedFunction(func_data, "legacy", "scoped_context")
        elif callable(func_data):
            # Regular callable (Python function, bound method, etc.)
            return ResolvedFunction(func_data, "callable", "scoped_context")
        else:
            self.logger.warning(f"Found non-callable object '{type(func_data)}' for function '{name_info.full_key}'")
            return None

    def _resolve_from_registry(self, name_info: FunctionNameInfo, registry: Any) -> ResolvedFunction | None:
        """Resolve function from function registry.

        Args:
            name_info: Parsed function name information
            registry: The function registry

        Returns:
            Resolved function from registry, or None if not found
        """
        if not registry:
            return None

        try:
            # Try original name first
            if registry.has_function(name_info.original_name):
                return ResolvedFunction(
                    func=None,  # Registry functions don't expose the actual function object
                    func_type="registry",
                    source="registry",
                    metadata={"resolved_name": name_info.original_name, "original_name": name_info.original_name}
                )

            # Try base function name
            if registry.has_function(name_info.func_name):
                return ResolvedFunction(
                    func=None,  # Registry functions don't expose the actual function object
                    func_type="registry",
                    source="registry",
                    metadata={"resolved_name": name_info.func_name, "original_name": name_info.original_name}
                )

        except Exception as e:
            self.logger.debug(f"Registry lookup failed for '{name_info.original_name}': {e}")

        return None

    def execute_resolved_function(self, resolved_func: ResolvedFunction, context: SandboxContext, 
                                 evaluated_args: list, evaluated_kwargs: dict, func_name: str) -> Any:
        """Execute a resolved function with the given arguments.

        Args:
            resolved_func: The resolved function information
            context: The execution context
            evaluated_args: List of evaluated positional arguments
            evaluated_kwargs: Dictionary of evaluated keyword arguments
            func_name: The function name for error reporting

        Returns:
            The result of the function execution

        Raises:
            SandboxError: If function execution fails
        """
        if resolved_func.func_type == "sandbox":
            # SandboxFunction - use execute method
            raw_result = resolved_func.func.execute(context, *evaluated_args, **evaluated_kwargs)
            return self.executor._assign_and_coerce_result(raw_result, func_name)

        elif resolved_func.func_type == "legacy":
            # Legacy user-defined function dict
            raw_result = self.executor._execute_user_defined_function(resolved_func.func, evaluated_args, context)
            return self.executor._assign_and_coerce_result(raw_result, func_name)

        elif resolved_func.func_type == "callable":
            # Regular callable
            raw_result = resolved_func.func(*evaluated_args, **evaluated_kwargs)
            return self.executor._assign_and_coerce_result(raw_result, func_name)

        elif resolved_func.source == "registry":
            # Registry function - delegate to the registry's call method which handles context injection properly
            registry = self.executor.function_registry
            if registry:
                # Use the resolved name (which worked) rather than the original name (which might not work)
                resolved_name = resolved_func.metadata.get("resolved_name", resolved_func.metadata.get("original_name", func_name))
                raw_result = registry.call(resolved_name, context, None, *evaluated_args, **evaluated_kwargs)
            else:
                raise SandboxError(f"No function registry available to execute function '{func_name}'")
            return self.executor._assign_and_coerce_result(raw_result, func_name)

        else:
            raise SandboxError(f"Unknown function type '{resolved_func.func_type}' for function '{func_name}'")

    def list_available_functions(self, namespace: str = None) -> list[str]:
        """List available functions in the given namespace.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            List of available function names
        """
        available = []

        # Get functions from context
        for var_name in self.context.list_variables():
            if "." in var_name:
                ns, func_name = var_name.split(".", 1)
                if namespace is None or ns == namespace:
                    available.append(var_name)

        # Get functions from registry
        for func_name in FunctionRegistry.list_functions():
            if namespace is None or namespace == "registry":
                available.append(f"registry.{func_name}")

        return sorted(available)
