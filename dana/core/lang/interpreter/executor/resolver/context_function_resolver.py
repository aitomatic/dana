"""
Context Function Resolver - User-defined functions with scope hierarchy.

This resolver handles functions defined in the context, following the proper
scope hierarchy: local → private → system → public.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import FunctionType, ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext

from .base_resolver import FunctionResolverInterface


class ContextFunctionResolver(FunctionResolverInterface):
    """
    Resolver for user-defined functions in the execution context.

    This resolver handles functions stored in the context with proper
    scope hierarchy resolution: local → private → system → public.
    Priority: 20 (after registry functions).
    """

    def get_priority(self) -> int:
        """Get resolver priority (after registry).

        Returns:
            Priority level 20 (medium-high priority)
        """
        return 20

    def can_resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this resolver can potentially resolve the function.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            True if context is available
        """
        return context is not None

    def resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Resolve function from context using proper scope hierarchy.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            Resolved function from context, or None if not found
        """
        if not context:
            return None

        # If function name specifies a scope (e.g., "local:my_func", "private:my_func"), only check that scope
        if name_info.namespace:
            return self._resolve_from_specific_scope(name_info, context)

        # For unscoped function names, try each scope in hierarchy order
        return self._resolve_from_scope_hierarchy(name_info, context)

    def _resolve_from_specific_scope(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Resolve function from a specific scope.

        Args:
            name_info: Parsed function name information (with namespace)
            context: The execution context

        Returns:
            ResolvedFunction if found, None otherwise
        """
        try:
            func_data = context.get(name_info.full_key)
            if func_data is not None:
                self.logger.debug(f"Found function in {name_info.namespace} scope: {name_info.full_key}")
                return self._create_resolved_function_from_context(func_data, name_info)
        except Exception as e:
            self.logger.debug(f"Failed to get function from {name_info.namespace} scope: {e}")

        return None

    def _resolve_from_scope_hierarchy(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Resolve function using scope hierarchy: local → private → system → public.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction if found, None otherwise
        """
        # Define scope hierarchy (order matters!)
        scope_hierarchy = ["local", "private", "system", "public"]

        for scope in scope_hierarchy:
            try:
                scoped_key = f"{scope}:{name_info.func_name}"
                func_data = context.get(scoped_key)
                if func_data is not None:
                    self.logger.debug(f"Found function in {scope} scope: {scoped_key}")
                    # Create resolved info with the actual scope found
                    resolved_info = FunctionNameInfo(
                        original_name=name_info.original_name, func_name=name_info.func_name, namespace=scope, full_key=scoped_key
                    )
                    return self._create_resolved_function_from_context(func_data, resolved_info)
            except Exception as e:
                self.logger.debug(f"Failed to check {scope} scope: {e}")
                continue

        return None

    def _create_resolved_function_from_context(self, func_data, name_info: FunctionNameInfo) -> ResolvedFunction:
        """Create a ResolvedFunction from context data.

        Args:
            func_data: Function data from context
            name_info: Function name information

        Returns:
            ResolvedFunction with appropriate type and metadata
        """
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        from dana.core.lang.interpreter.functions.python_function import PythonFunction
        from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction

        self.logger.debug(f"Creating resolved function for '{name_info.full_key}', type: {type(func_data)}")

        # Check if this is a decorated function (has __wrapped__ attribute)
        if hasattr(func_data, "__wrapped__"):
            # Decorated functions should be treated as CALLABLE
            func_type = FunctionType.CALLABLE
        else:
            # Determine function type based on actual type
            if isinstance(func_data, DanaFunction | SandboxFunction):
                func_type = FunctionType.DANA
            elif isinstance(func_data, PythonFunction):
                func_type = FunctionType.PYTHON
            elif callable(func_data):
                func_type = FunctionType.CALLABLE
            else:
                # This should never happen for functions
                raise ValueError(f"Invalid function type '{type(func_data)}' for function '{name_info.full_key}'")

        return ResolvedFunction(
            func=func_data,
            func_type=func_type,
            source="context",
            metadata={
                "resolved_name": name_info.full_key,
                "original_name": name_info.original_name,
                "scope": name_info.namespace,
                "context_lookup": True,
            },
        )
