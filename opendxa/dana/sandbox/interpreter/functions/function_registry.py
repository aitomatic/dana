"""
Unified Function Registry for DANA and Python functions.

This registry supports namespacing, type tagging, and unified dispatch for both DANA and Python functions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from inspect import signature
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from opendxa.dana.common.runtime_scopes import RuntimeScopes

if TYPE_CHECKING:
    from opendxa.dana.sandbox.sandbox_context import SandboxContext


@dataclass
class FunctionMetadata:
    """Metadata for registered functions."""

    context_aware: bool = False  # Whether function accepts context as first arg
    is_public: bool = True  # Whether function is publicly accessible
    doc: Optional[str] = None  # Function documentation
    source_file: Optional[str] = None  # Source file where function is defined


class FunctionRegistry:
    def __init__(self):
        # {namespace: {name: (func, type, metadata)}}
        self._functions: Dict[str, Dict[str, Tuple[Callable, str, FunctionMetadata]]] = {}

    def _remap_namespace_and_name(self, ns: Optional[str] = None, name: Optional[str] = None) -> Tuple[str, str]:
        """
        Normalize and validate function namespace/name pairs for consistent registration and lookup.

        Goal:
            Ensure that all function registrations and lookups use a consistent (namespace, name) tuple,
            regardless of how the user specifies them (with or without explicit namespace, or with a dotted name).
            This prevents ambiguity and errors in the function registry, making function dispatch robust and predictable.

        Logic:
            - If no namespace is provided and the name contains a dot (e.g., 'math.sin'),
              attempt to split the name into namespace and function name. If the extracted
              namespace is not valid (not in RuntimeScopes.ALL), treat the entire name as
              a local function (namespace=None, name unchanged).
            - If a namespace is provided (non-empty), the namespace and name are returned as-is,
              regardless of whether the name contains a dot.
            - After remapping, if the namespace is still None or empty, it defaults to 'local'.

            ns          name            -> remapped_ns  remapped_name
            ------------------------------------------------------------
            None        foo             -> local        foo
                        foo             -> local        foo
            local       foo             -> local        foo
            None        math.sin        -> local        math.sin
            None        local.bar       -> local        bar
            None        system.baz      -> system       baz
            private     foo             -> private      foo
            private     math.sin        -> private      math.sin
                        public.x        -> public       x
            None        foo.bar.baz     -> local        foo.bar.baz
            system      foo.bar         -> system       foo.bar

        Args:
            ns: The namespace string (may be empty or None)
            name: The function name, which may include a namespace prefix (e.g., 'math.sin')

        Returns:
            A tuple of (remapped_namespace, remapped_name), where remapped_namespace is always non-empty.
        """
        rns = ns
        rname = name
        if name and "." in name:
            if not ns or ns == "":
                # If no namespace provided but name contains dot, split into namespace and name
                rns, rname = name.split(".", 1)
                if rns not in RuntimeScopes.ALL:
                    # not a valid namespace
                    rns, rname = None, name

        rns = rns or "local"

        return rns, rname or ""

    def register(
        self,
        name: str,
        func: Callable,
        namespace: Optional[str] = None,
        func_type: str = "dana",
        metadata: Optional[FunctionMetadata] = None,
        overwrite: bool = False,
    ) -> None:
        """Register a function with optional namespace and metadata.

        Args:
            name: Function name
            func: The callable function
            namespace: Optional namespace (defaults to global)
            func_type: Type of function ("dana" or "python")
            metadata: Optional function metadata
            overwrite: Whether to allow overwriting existing functions

        Raises:
            ValueError: If function already exists and overwrite=False
        """
        ns, name = self._remap_namespace_and_name(namespace, name)
        if ns not in self._functions:
            self._functions[ns] = {}

        if name in self._functions[ns] and not overwrite:
            raise ValueError(f"Function '{name}' already exists in namespace '{ns}'. Use overwrite=True to force.")

        # Auto-detect context awareness for Python functions
        if not metadata:
            sig = signature(func)
            params = list(sig.parameters.values())
            is_context_aware = len(params) > 0 and params[0].name == "ctx"
            metadata = FunctionMetadata(context_aware=is_context_aware)

        self._functions[ns][name] = (func, func_type, metadata)

    def resolve(self, name: str, namespace: Optional[str] = None) -> Tuple[Callable, str, FunctionMetadata]:
        """Resolve a function by name and namespace.

        Args:
            name: Function name to resolve
            namespace: Optional namespace

        Returns:
            Tuple of (function, type, metadata)

        Raises:
            KeyError: If function not found
        """
        ns, name = self._remap_namespace_and_name(namespace, name)
        if ns in self._functions and name in self._functions[ns]:
            return self._functions[ns][name]
        raise KeyError(f"Function '{name}' not found in namespace '{ns}'")

    def call(
        self,
        name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional["SandboxContext"] = None,
        local_context: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> Any:
        """Call a function with arguments and optional context.

        Args:
            name: Function name
            args: Positional arguments
            kwargs: Keyword arguments
            context: Optional context object
            local_context: Optional local context object
            namespace: Optional namespace

        Returns:
            Function result

        Raises:
            KeyError: If function not found
            TypeError: If argument binding fails
        """
        func, func_type, metadata = self.resolve(name, namespace)
        call_args = args if args is not None else []
        call_kwargs = kwargs if kwargs is not None else {}

        try:
            # Always inject context for context-aware functions
            if metadata.context_aware:
                return func(
                    context,
                    local_context,
                    *call_args,
                    **call_kwargs,
                )
            return func(*call_args, **call_kwargs)
        except TypeError as e:
            # Re-raise with more descriptive error message
            raise TypeError(f"Error calling function '{name}': {str(e)}")

    def list(self, namespace: Optional[str] = None) -> List[str]:
        """List all functions in a namespace.

        Args:
            namespace: Optional namespace to list from

        Returns:
            List of function names
        """
        ns = namespace or ""
        return list(self._functions.get(ns, {}).keys())

    def has(self, name: str, namespace: Optional[str] = None) -> bool:
        """Check if a function exists.

        Args:
            name: Function name
            namespace: Optional namespace

        Returns:
            True if function exists
        """
        ns, name = self._remap_namespace_and_name(namespace, name)
        return ns in self._functions and name in self._functions[ns]

    def get_metadata(self, name: str, namespace: Optional[str] = None) -> FunctionMetadata:
        """Get metadata for a function.

        Args:
            name: Function name
            namespace: Optional namespace

        Returns:
            Function metadata

        Raises:
            KeyError: If function not found
        """
        _, _, metadata = self.resolve(name, namespace)
        return metadata
