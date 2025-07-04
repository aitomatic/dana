"""
Fallback Resolver - Error recovery and edge cases.

This resolver provides fallback resolution strategies and handles
edge cases that other resolvers cannot handle.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo
from dana.core.lang.interpreter.executor.function_resolver import FunctionType, ResolvedFunction
from dana.core.lang.sandbox_context import SandboxContext

from .base_resolver import FunctionResolverInterface


class FallbackResolver(FunctionResolverInterface):
    """
    Fallback resolver for edge cases and error recovery.

    This resolver handles cases that other resolvers cannot handle,
    including name variations, typo corrections, and other recovery
    strategies.
    Priority: 40 (lowest priority - only used when others fail).
    """

    def get_priority(self) -> int:
        """Get resolver priority (lowest priority).

        Returns:
            Priority level 40 (lowest priority)
        """
        return 40

    def can_resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> bool:
        """Check if this resolver can potentially resolve the function.

        The fallback resolver can always attempt resolution as a last resort.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            Always True (fallback can always try)
        """
        return True

    def resolve(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Attempt fallback resolution strategies.

        Args:
            name_info: Parsed function name information
            context: The execution context

        Returns:
            ResolvedFunction if fallback succeeds, None otherwise
        """
        self.logger.debug(f"FallbackResolver attempting resolution for: {name_info.original_name}")

        # Strategy 1: Try name variations and common misspellings
        resolved = self._try_name_variations(name_info, context)
        if resolved:
            return resolved

        # Strategy 2: Try cross-namespace lookup
        resolved = self._try_cross_namespace_lookup(name_info, context)
        if resolved:
            return resolved

        # Strategy 3: Try backward compatibility patterns
        resolved = self._try_backward_compatibility(name_info, context)
        if resolved:
            return resolved

        # All fallback strategies failed
        self.logger.debug(f"All fallback strategies failed for: {name_info.original_name}")
        return None

    def _try_name_variations(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Try common name variations and misspellings.

        Args:
            name_info: Function name information
            context: The execution context

        Returns:
            ResolvedFunction if variation found, None otherwise
        """
        variations = self._generate_name_variations(name_info.func_name)

        for variation in variations:
            try:
                # Try in local scope first
                variation_key = f"local:{variation}"
                func_data = context.get(variation_key)
                if func_data is not None:
                    self.logger.debug(f"Found function variation: {variation}")
                    return self._create_fallback_resolved_function(func_data, name_info, f"name_variation:{variation}")
            except Exception:
                continue

        return None

    def _try_cross_namespace_lookup(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Try looking in all namespaces regardless of scope.

        Args:
            name_info: Function name information
            context: The execution context

        Returns:
            ResolvedFunction if found in any namespace, None otherwise
        """
        # Try all possible namespace combinations
        namespaces = ["local", "private", "system", "public"]

        for namespace in namespaces:
            try:
                cross_key = f"{namespace}:{name_info.func_name}"
                func_data = context.get(cross_key)
                if func_data is not None:
                    self.logger.debug(f"Found function in cross-namespace lookup: {cross_key}")
                    return self._create_fallback_resolved_function(func_data, name_info, f"cross_namespace:{namespace}")
            except Exception:
                continue

        return None

    def _try_backward_compatibility(self, name_info: FunctionNameInfo, context: SandboxContext) -> ResolvedFunction | None:
        """Try backward compatibility patterns.

        Args:
            name_info: Function name information
            context: The execution context

        Returns:
            ResolvedFunction if backward compatible pattern found, None otherwise
        """
        # Try old-style dot notation as key
        if "." in name_info.original_name:
            try:
                # Try the original dot notation as a direct key
                func_data = context.get(name_info.original_name)
                if func_data is not None:
                    self.logger.debug(f"Found function with backward compatibility: {name_info.original_name}")
                    return self._create_fallback_resolved_function(func_data, name_info, "backward_compatibility:dot_notation")
            except Exception:
                pass

        return None

    def _generate_name_variations(self, func_name: str) -> list[str]:
        """Generate common name variations for typo tolerance.

        Args:
            func_name: Base function name

        Returns:
            List of name variations to try
        """
        variations = []

        # Common typo patterns
        if len(func_name) > 3:
            # Try with common suffixes/prefixes
            variations.extend(
                [
                    f"{func_name}s",  # plural
                    f"{func_name}_func",  # with _func suffix
                    f"_{func_name}",  # with _ prefix
                ]
            )

        # Try case variations
        variations.extend(
            [
                func_name.lower(),
                func_name.upper(),
                func_name.capitalize(),
            ]
        )

        # Remove duplicates and original name
        variations = list(set(variations))
        if func_name in variations:
            variations.remove(func_name)

        return variations

    def _create_fallback_resolved_function(
        self, func_data, original_name_info: FunctionNameInfo, fallback_strategy: str
    ) -> ResolvedFunction:
        """Create a resolved function from fallback data.

        Args:
            func_data: Function data found
            original_name_info: Original function name information
            fallback_strategy: Which fallback strategy succeeded

        Returns:
            ResolvedFunction with fallback metadata
        """
        # Import here to avoid circular imports
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction
        from dana.core.lang.interpreter.functions.python_function import PythonFunction
        from dana.core.lang.interpreter.functions.sandbox_function import SandboxFunction

        # Determine function type
        if isinstance(func_data, DanaFunction | SandboxFunction):
            func_type = FunctionType.DANA
        elif isinstance(func_data, PythonFunction):
            func_type = FunctionType.PYTHON
        elif callable(func_data):
            func_type = FunctionType.CALLABLE
        else:
            # Fallback to callable if we're not sure
            func_type = FunctionType.CALLABLE

        return ResolvedFunction(
            func=func_data,
            func_type=func_type,
            source="fallback",
            metadata={
                "resolved_name": original_name_info.original_name,
                "original_name": original_name_info.original_name,
                "fallback_strategy": fallback_strategy,
                "fallback_resolution": True,
            },
        )
