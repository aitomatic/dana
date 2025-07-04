"""
Composed Function Resolver - Function composition support.

This resolver handles function composition scenarios where functions
are being combined with pipe operators or other composition mechanisms.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import FunctionType, ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext

from .base_resolver import FunctionResolverInterface


class ComposedFunctionResolver(FunctionResolverInterface):
    """
    Resolver for function composition scenarios.

    This resolver handles cases where functions are being composed
    together, particularly in pipe operations where lazy resolution
    might be needed.
    Priority: 30 (lower than core and context functions).
    """

    def get_priority(self) -> int:
        """Get resolver priority (after core and context).

        Returns:
            Priority level 30 (medium priority)
        """
        return 30

    def can_resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this resolver can potentially resolve the function.

        This resolver currently acts as a fallback for lazy resolution
        in function composition scenarios.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            True if this might be a composition scenario
        """
        # For now, this resolver is primarily for future composition support
        # It can attempt lazy resolution for functions that might be defined later
        return True

    def resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Attempt to resolve function for composition scenarios.

        This resolver currently provides lazy resolution support for
        function composition. In the future, it could handle more
        sophisticated composition patterns.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction if this is a valid composition scenario, None otherwise
        """
        # For now, this resolver doesn't resolve functions directly
        # It's a placeholder for future composition features

        # Check if this might be a composed function in context
        if self._is_potential_composed_function(name_info, context):
            return self._create_lazy_resolved_function(name_info)

        return None

    def _is_potential_composed_function(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this might be a composed function that needs lazy resolution.

        Args:
            name_info: Function name information
            context: The execution context

        Returns:
            True if this could be a composed function
        """
        # Look for signs that this might be a composed function
        # For example, functions with certain naming patterns or
        # functions that are referenced in composition contexts

        # This is a simplified check - in practice, this would be more sophisticated
        return False  # Disabled for now until composition features are needed

    def _create_lazy_resolved_function(self, name_info: FunctionNameInfo) -> ResolvedFunction:
        """Create a lazy resolved function for composition.

        Args:
            name_info: Function name information

        Returns:
            ResolvedFunction with lazy resolution metadata
        """
        # Create a placeholder resolved function that can be resolved later
        # This would be used in function composition scenarios
        return ResolvedFunction(
            func=None,  # Will be resolved later
            func_type=FunctionType.DANA,  # Assume Dana function for composition
            source="composition",
            metadata={
                "resolved_name": name_info.original_name,
                "original_name": name_info.original_name,
                "lazy_resolution": True,
                "composition_ready": True,
            },
        )
