"""
Optimized identifier resolution for Dana expressions.

This module provides a high-performance identifier resolver that consolidates
the complex identifier resolution strategies from ExpressionExecutor with
caching and optimization.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.common.exceptions import StateError
from dana.common.mixins.loggable import Loggable
from dana.common.utils.misc import Misc
from dana.core.lang.ast import Identifier
from dana.core.lang.sandbox_context import SandboxContext


class IdentifierResolver(Loggable):
    """Optimized identifier resolver with caching and unified strategies.

    This resolver consolidates multiple resolution strategies:
    1. Direct context lookup
    2. Cross-scope variable search
    3. Scoped identifier resolution (local:var, private:var)
    4. Dotted attribute access (obj.attr.field)
    5. Function registry resolution via unified dispatcher
    6. Legacy dot notation compatibility

    Performance optimizations:
    - LRU cache for frequently accessed identifiers
    - Early termination for common patterns
    - Optimized scope traversal order
    - Cached function registry lookups
    """

    def __init__(self, function_executor=None):
        """Initialize the identifier resolver.

        Args:
            function_executor: Reference to FunctionExecutor for unified dispatcher access
        """
        super().__init__()
        self.function_executor = function_executor
        self._identifier_cache = {}  # Simple cache for identifier resolution
        self._cache_hits = 0
        self._cache_misses = 0

    def resolve_identifier(self, node: Identifier, context: SandboxContext) -> Any:
        """Resolve an identifier to its value using optimized strategies.

        Args:
            node: The identifier node to resolve
            context: The execution context

        Returns:
            The resolved value of the identifier

        Raises:
            StateError: If the identifier cannot be resolved
        """
        name = node.name

        # Strategy 1: Check cache first for performance
        # Cache disabled: context hashing causes incorrect results
        # TODO: Implement stable context fingerprinting for cache keys

        self._cache_misses += 1
        self.debug(f"Resolving identifier '{name}' (cache miss)")

        try:
            # Strategy 2: Try direct context lookup (most common case)
            result = self._try_direct_context_lookup(name, context)
            if result is not None:
                return result

            # Strategy 3: Try cross-scope search for unscoped variables
            if "." not in name and ":" not in name:
                result = self._try_cross_scope_search(name, context)
                if result is not None:
                    return result

            # Strategy 4: Try scoped identifier resolution
            elif ":" in name or "." in name:
                result = self._try_scoped_resolution(name, context)
                if result is not None:
                    return result

            # Strategy 5: Try function registry via unified dispatcher
            result = self._try_function_registry_resolution(name, context)
            if result is not None:
                # Don't cache function objects as they may change
                return result

            # Strategy 6: Try dotted attribute access fallback
            result = self._try_dotted_attribute_access(name, context)
            if result is not None:
                return result

            # Strategy 7: Try struct type name resolution
            result = self._try_struct_type_resolution(name)
            if result is not None:
                # Don't cache struct type names as they may change
                return result

            # All strategies failed - gracefully return None for undefined variables
            self.debug(f"Identifier '{name}' not found - returning None gracefully")
            return None

        except Exception as e:
            # Don't cache exceptions
            self.debug(f"Failed to resolve identifier '{name}': {e}")
            raise

    def _try_direct_context_lookup(self, name: str, context: SandboxContext) -> Any | None:
        """Try direct context lookup using context.get()."""
        try:
            result = context.get(name)
            if result is not None:
                self.debug(f"Found '{name}' via direct context lookup")
                return result
        except StateError:
            pass
        return None

    def _try_cross_scope_search(self, name: str, context: SandboxContext) -> Any | None:
        """Search for unscoped variable across all scopes in priority order."""
        # Search in priority order: local -> private -> public -> system
        scope_priority = ["local", "private", "public", "system"]

        for scope in scope_priority:
            try:
                value = context.get_from_scope(name, scope=scope)
                if value is not None:
                    self.debug(f"Found '{name}' in scope '{scope}' via cross-scope search")
                    return value
            except StateError:
                continue
        return None

    def _try_scoped_resolution(self, name: str, context: SandboxContext) -> Any | None:
        """Resolve scoped identifiers (local:var or local.var format)."""
        # Handle colon notation (modern): "local:var" or "system:func"
        if ":" in name:
            return self._resolve_colon_notation(name, context)

        # Handle dot notation (legacy): "local.var" or "system.func"
        elif "." in name:
            return self._resolve_dot_notation(name, context)

        return None

    def _resolve_colon_notation(self, name: str, context: SandboxContext) -> Any | None:
        """Resolve colon notation identifiers (local:var)."""
        parts = name.split(":", 1)
        if len(parts) != 2:
            return None

        scope_name, var_name = parts
        if scope_name not in ["local", "private", "public", "system"]:
            return None

        # Handle simple scoped variables
        if "." not in var_name:
            try:
                value = context.get_from_scope(var_name, scope=scope_name)
                if value is not None:
                    self.debug(f"Found '{name}' via colon notation resolution")
                    return value
            except StateError:
                pass

            # Fallback: search in other scopes
            return self._try_fallback_scope_search(var_name, scope_name, context)

        # Handle complex scoped attributes (local:obj.attr)
        else:
            return self._resolve_scoped_attribute_access(var_name, scope_name, context)

    def _resolve_dot_notation(self, name: str, context: SandboxContext) -> Any | None:
        """Resolve dot notation identifiers (local.var) - legacy compatibility."""
        parts = name.split(".", 1)
        if len(parts) != 2:
            return None

        scope_name, var_name = parts
        if scope_name not in ["local", "private", "public", "system"]:
            # Not a scoped variable, try dotted attribute access
            return self._try_dotted_attribute_access(name, context)

        # Handle simple scoped variables (convert to colon notation internally)
        if "." not in var_name:
            try:
                value = context.get_from_scope(var_name, scope=scope_name)
                if value is not None:
                    self.debug(f"Found '{name}' via dot notation resolution")
                    return value
            except StateError:
                pass

            # Fallback: search in other scopes
            return self._try_fallback_scope_search(var_name, scope_name, context)

        # Handle complex scoped attributes (local.obj.attr)
        else:
            return self._resolve_scoped_attribute_access(var_name, scope_name, context)

    def _try_fallback_scope_search(self, var_name: str, specified_scope: str, context: SandboxContext) -> Any | None:
        """Search for variable in other scopes if not found in specified scope."""
        for scope in ["local", "private", "public", "system"]:
            if scope != specified_scope:  # Don't re-search the same scope
                try:
                    value = context.get_from_scope(var_name, scope=scope)
                    if value is not None:
                        self.debug(f"Found '{var_name}' in fallback scope '{scope}'")
                        return value
                except StateError:
                    continue
        return None

    def _resolve_scoped_attribute_access(self, var_name: str, scope_name: str, context: SandboxContext) -> Any | None:
        """Resolve scoped attribute access (local:obj.attr or local.obj.attr)."""
        base_var = var_name.split(".", 1)[0]
        attribute_path = var_name.split(".", 1)[1]

        # Try to find base variable in specified scope first
        try:
            base_value = context.get_from_scope(base_var, scope=scope_name)
            if base_value is not None:
                return self._access_attribute_path(base_value, attribute_path)
        except (StateError, AttributeError):
            pass

        # Fallback: search for base variable in other scopes
        for scope in ["local", "private", "public", "system"]:
            if scope != scope_name:
                try:
                    base_value = context.get_from_scope(base_var, scope=scope)
                    if base_value is not None:
                        return self._access_attribute_path(base_value, attribute_path)
                except (StateError, AttributeError):
                    continue
        return None

    def _access_attribute_path(self, base_value: Any, attribute_path: str) -> Any:
        """Access a dotted attribute path on a base value."""
        result = base_value
        for attr in attribute_path.split("."):
            result = getattr(result, attr)
        return result

    def _try_function_registry_resolution(self, name: str, context: SandboxContext) -> Any | None:
        """Try to resolve identifier using the unified function dispatcher."""
        if not (
            self.function_executor and hasattr(self.function_executor, "unified_dispatcher") and self.function_executor.unified_dispatcher
        ):
            return None

        try:
            from dana.core.lang.interpreter.executor.function_name_utils import FunctionNameInfo

            # Parse the identifier name into FunctionNameInfo components
            if ":" in name:
                # Modern colon notation: "local:func" or "system:func"
                parts = name.split(":", 1)
                namespace = parts[0]
                func_name = parts[1]
                full_key = name
            elif "." in name:
                # Legacy dot notation: "local.func" or "system.func"
                parts = name.split(".", 1)
                namespace = parts[0]
                func_name = parts[1]
                full_key = f"{namespace}:{func_name}"
            else:
                # Unscoped function name
                namespace = None
                func_name = name
                full_key = name

            name_info = FunctionNameInfo(name, func_name, namespace, full_key)

            # Try to resolve using the unified dispatcher
            resolved_func = self.function_executor.unified_dispatcher.resolve_function(name_info, context)
            if resolved_func:
                if resolved_func.func:
                    self.debug(f"Found '{name}' as function via unified dispatcher")
                    return resolved_func.func
                elif resolved_func.func_type.value == "registry":
                    # Create callable wrapper for registry functions
                    return self._create_registry_wrapper(name, resolved_func, context)
                else:
                    return resolved_func

        except Exception as e:
            self.debug(f"Function registry resolution failed for '{name}': {e}")

        return None

    def _create_registry_wrapper(self, name: str, resolved_func: Any, context: SandboxContext) -> Any:
        """Create a callable wrapper for registry functions."""

        def registry_function(*args, **kwargs):
            if self.function_executor and hasattr(self.function_executor, "function_registry"):
                registry = self.function_executor.function_registry
                resolved_name = resolved_func.metadata.get("resolved_name", name)
                if registry:
                    return registry.call(resolved_name, context, "", *args, **kwargs)
            raise RuntimeError("No function registry available")

        self.debug(f"Created registry wrapper for '{name}'")
        return registry_function

    def _try_dotted_attribute_access(self, name: str, context: SandboxContext) -> Any | None:
        """Try dotted attribute access as a fallback strategy."""
        parts = name.split(".")
        if len(parts) < 2:
            return None

        self.debug(f"Trying dotted attribute access for '{name}'")

        result = None
        for _i, part in enumerate(parts):
            if result is None:
                # Look for base variable in context state
                if part in context._state:
                    result = context._state[part]
                    self.debug(f"Found base variable '{part}' in context state")
                else:
                    # Try to find the variable in any scope
                    for scope in ["local", "private", "public", "system"]:
                        try:
                            result = context.get_from_scope(part, scope=scope)
                            if result is not None:
                                self.debug(f"Found base variable '{part}' in scope '{scope}'")
                                break
                        except Exception:
                            continue

                    if result is None:
                        self.debug(f"Could not find base variable '{part}'")
                        return None
            else:
                # Access attribute on current result
                try:
                    result = Misc.get_field(result, part)
                    self.debug(f"Accessed attribute '{part}' successfully")
                except Exception as e:
                    self.debug(f"Failed to access attribute '{part}': {e}")
                    return None

        return result

    def _try_struct_type_resolution(self, name: str) -> Any | None:
        """Try to resolve identifier as a struct type name.

        Args:
            name: The identifier name to check

        Returns:
            The struct type name string if found, None otherwise
        """
        try:
            from dana.registry import TYPE_REGISTRY

            # Check if this is a registered struct type name
            if TYPE_REGISTRY.exists(name):
                self.debug(f"Found '{name}' as struct type name")
                return name  # Return the string name for struct types

        except ImportError:
            # Struct system not available, continue without it
            pass
        except Exception as e:
            self.debug(f"Struct type resolution failed for '{name}': {e}")

        return None

    def _cache_result(self, cache_key: tuple, result: Any) -> None:
        """Cache a resolution result (simple LRU with size limit)."""
        # Simple cache with size limit to prevent memory growth
        if len(self._identifier_cache) > 1000:  # Configurable limit
            # Remove oldest entries (simple FIFO for now)
            oldest_key = next(iter(self._identifier_cache))
            del self._identifier_cache[oldest_key]

        self._identifier_cache[cache_key] = result

    def clear_cache(self) -> None:
        """Clear the identifier resolution cache."""
        self._identifier_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self.debug("Identifier resolution cache cleared")

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get cache performance statistics."""
        total_lookups = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_lookups": total_lookups,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._identifier_cache),
        }
