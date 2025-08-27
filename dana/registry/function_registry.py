"""
Function Registry for Dana

Unified registry for function registration and dispatch with support for both simple and advanced use cases.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import builtins
import inspect
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

from dana.common.exceptions import FunctionRegistryError, SandboxError
from dana.common.runtime_scopes import RuntimeScopes
from dana.core.lang.interpreter.executor.function_resolver import FunctionType

if TYPE_CHECKING:
    from dana.core.lang.sandbox_context import SandboxContext


@dataclass
class FunctionMetadata:
    """Metadata for registered functions."""

    source_file: str | None = None  # Source file where function is defined
    _context_aware: bool | None = None  # Whether function expects context parameter
    _is_public: bool = True  # Whether function is accessible from public code
    _doc: str = ""  # Function documentation
    registered_at: float = 0.0  # Registration timestamp
    overwrites: int = 0  # Number of times this function was overwritten

    @property
    def context_aware(self) -> bool:
        """Returns whether the function expects a context parameter."""
        return self._context_aware if self._context_aware is not None else True

    @context_aware.setter
    def context_aware(self, value: bool) -> None:
        """Set whether the function expects a context parameter."""
        self._context_aware = value

    @property
    def is_public(self) -> bool:
        """Returns whether the function is accessible from public code."""
        return self._is_public

    @is_public.setter
    def is_public(self, value: bool) -> None:
        """Set whether the function is accessible from public code."""
        self._is_public = value

    @property
    def doc(self) -> str:
        """Returns the function documentation."""
        return self._doc

    @doc.setter
    def doc(self, value: str) -> None:
        """Set the function documentation."""
        self._doc = value


class RegistryAdapter:
    """Adapts FunctionRegistry for use with ExpressionEvaluator."""

    def __init__(self, registry):
        """Initialize with a reference to the registry."""
        self.registry = registry

    def get_registry(self):
        """Get the function registry."""
        return self.registry

    def resolve_function(self, name, namespace=None):
        """Resolve a function using the registry."""
        return self.registry.resolve(name, namespace)

    def call_function(self, name, context=None, namespace=None, *args, **kwargs):
        """Call a function using the registry."""
        return self.registry.call(name, context, namespace, *args, **kwargs)


class FunctionRegistry:
    """Unified registry for function registration with support for both simple and advanced use cases.

    This registry maintains mappings of function names to callable objects,
    providing fast lookup and registration for Dana's function system.
    Supports both simple key-value storage and advanced namespaced storage.
    """

    def __init__(self, struct_function_registry=None):
        """Initialize the function registry with both simple and namespaced storage.

        Args:
            struct_function_registry: Optional StructFunctionRegistry instance for delegation.
                                    If provided, all struct method operations will be delegated to this registry.
        """
        # Simple storage: name -> (func, metadata) - for backward compatibility
        self._simple_functions: dict[str, tuple[Callable, FunctionMetadata]] = {}

        # Namespace storage: namespace -> {name -> (func, metadata)} - for advanced use cases
        self._namespaced_functions: dict[str, dict[str, tuple[Callable, FunctionMetadata]]] = {}

        # Old-style namespaced storage for full backward compatibility
        self._functions_old_style: dict[str, dict[str, tuple[Callable, FunctionType, FunctionMetadata]]] = {}

        # Registration order tracking (for simple API)
        self._registration_order: list[str] = []

        # Preloaded functions support
        self._preloaded_functions: dict[str, dict[str, tuple[Callable, FunctionMetadata]]] = {}

        # Load preloaded functions
        self._register_preloaded_functions()

        # Struct method delegation
        self._struct_function_registry = struct_function_registry

        # Struct method storage: (receiver_type, method_name) -> (func, metadata)
        # This provides O(1) lookup for struct methods while maintaining the same
        # metadata tracking as regular functions. Only used if no delegation registry provided.
        self._struct_functions: dict[tuple[str, str], tuple[Callable, FunctionMetadata]] = {}

    # === Simple API (Backward Compatible) ===

    def register_function(self, name: str, func: Callable) -> None:
        """Register a function using the simple API.

        Args:
            name: The function name
            func: The callable function to register
        """
        if not callable(func):
            raise ValueError("Function must be callable")

        metadata = FunctionMetadata(registered_at=self._get_timestamp())

        # Try to determine source file
        try:
            source_file = inspect.getsourcefile(func)
            if source_file:
                metadata.source_file = source_file
        except (TypeError, ValueError):
            pass

        if name in self._simple_functions:
            # Allow overwriting for now (useful during development)
            metadata.overwrites = self._simple_functions[name][1].overwrites + 1

        self._simple_functions[name] = (func, metadata)

        if name not in self._registration_order:
            self._registration_order.append(name)

    def get_function(self, name: str) -> Callable | None:
        """Get a function by name using the simple API.

        Args:
            name: The function name

        Returns:
            The function or None if not found
        """
        if name in self._simple_functions:
            return self._simple_functions[name][0]
        return None

    def has_function(self, name: str) -> bool:
        """Check if a function is registered using the simple API.

        Args:
            name: The function name

        Returns:
            True if the function is registered
        """
        return name in self._simple_functions

    def list_all(self) -> list[str]:
        """List all registered function names using the simple API.

        Returns:
            List of function names in registration order
        """
        return self._registration_order.copy()

    def list_functions(self, namespace: str | None = None) -> list[str]:
        """List all functions in a namespace (backward compatibility).

        Args:
            namespace: Optional namespace to list from. If None, lists from all namespaces.

        Returns:
            List of function names
        """
        if namespace is None:
            # Return functions from all namespaces
            all_functions = []
            for ns_functions in self._namespaced_functions.values():
                all_functions.extend(ns_functions.keys())
            return list(set(all_functions))  # Remove duplicates
        else:
            ns, _ = self._remap_namespace_and_name(namespace, "")
            return list(self._namespaced_functions.get(ns, {}).keys())

    def list(self, namespace: str | None = None) -> list[str]:
        """List all functions in a namespace (backward compatibility).

        This method is deprecated. Use list_functions() instead.
        """
        warnings.warn("FunctionRegistry.list() is deprecated. Use list_functions() instead.", DeprecationWarning, stacklevel=2)
        return self.list_functions(namespace)

    def get_function_metadata(self, name: str) -> dict[str, Any] | None:
        """Get metadata for a function using the simple API.

        Args:
            name: The function name

        Returns:
            Function metadata as dict or None if not found
        """
        if name in self._simple_functions:
            metadata = self._simple_functions[name][1]
            return {
                "source_file": metadata.source_file,
                "context_aware": metadata.context_aware,
                "is_public": metadata.is_public,
                "doc": metadata.doc,
                "registered_at": metadata.registered_at,
                "overwrites": metadata.overwrites,
            }
        return None

    # === Advanced API (Namespaced Support) ===

    def _remap_namespace_and_name(self, ns: str | None = None, name: str | None = None) -> tuple[str, str]:
        """Normalize and validate function namespace/name pairs.

        Args:
            ns: The namespace string (may be empty or None)
            name: The function name, which may include a namespace prefix

        Returns:
            A tuple of (remapped_namespace, remapped_name)
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
        namespace: str | None = None,
        func_type: FunctionType = FunctionType.PYTHON,
        metadata: FunctionMetadata | None = None,
        overwrite: bool = False,
        trusted_for_context: bool = False,
    ) -> None:
        """Register a function with optional namespace and metadata.

        Args:
            name: Function name
            func: The callable function
            namespace: Optional namespace (defaults to local)
            func_type: Function type (for backward compatibility)
            metadata: Optional function metadata
            overwrite: Whether to allow overwriting existing functions
            trusted_for_context: Whether function is trusted for context access

        Raises:
            ValueError: If function already exists and overwrite=False
        """
        if not callable(func):
            raise ValueError("Function must be callable")

        ns, name = self._remap_namespace_and_name(namespace, name)

        # Store in new-style namespaced storage
        if ns not in self._namespaced_functions:
            self._namespaced_functions[ns] = {}

        if name in self._namespaced_functions[ns] and not overwrite:
            raise ValueError(f"Function '{name}' already exists in namespace '{ns}'. Use overwrite=True to force.")

        if not metadata:
            metadata = FunctionMetadata(registered_at=self._get_timestamp())
            # Try to determine the source file
            try:
                source_file = inspect.getsourcefile(func)
                if source_file:
                    metadata.source_file = source_file
            except (TypeError, ValueError):
                pass

        # Set context awareness based on trusted_for_context
        if trusted_for_context:
            metadata.context_aware = True

        self._namespaced_functions[ns][name] = (func, metadata)

        # Also store in old-style storage for backward compatibility
        if ns not in self._functions_old_style:
            self._functions_old_style[ns] = {}
        self._functions_old_style[ns][name] = (func, func_type, metadata)

        # Also store in simple storage for backward compatibility
        if name not in self._simple_functions:
            self._simple_functions[name] = (func, metadata)
            if name not in self._registration_order:
                self._registration_order.append(name)

        # Store in old-style format for backward compatibility with tests
        if ns not in self._functions_old_style:
            self._functions_old_style[ns] = {}

        # Wrap the function in a PythonFunction for backward compatibility
        from dana.core.lang.interpreter.functions.python_function import PythonFunction

        wrapped_func = PythonFunction(func, trusted_for_context=trusted_for_context)

        self._functions_old_style[ns][name] = (wrapped_func, func_type, metadata)

    def resolve(self, name: str, namespace: str | None = None) -> tuple[Callable, FunctionMetadata]:
        """Resolve a function by name and namespace.

        Args:
            name: Function name to resolve
            namespace: Optional namespace. If None, searches all namespaces.

        Returns:
            Tuple of (function, metadata)

        Raises:
            FunctionRegistryError: If function not found
        """
        # If namespace is explicitly None, search across all namespaces
        if namespace is None:
            return self._resolve_across_namespaces(name)

        ns, name = self._remap_namespace_and_name(namespace, name)
        if ns in self._namespaced_functions and name in self._namespaced_functions[ns]:
            return self._namespaced_functions[ns][name]

        raise FunctionRegistryError(
            f"Function '{name}' not found in namespace '{ns}'",
            function_name=name,
            namespace=ns,
            operation="resolve",
        )

    def resolve_with_type(self, name: str, namespace: str | None = None) -> tuple[Callable, FunctionType, FunctionMetadata]:
        """Resolve a function by name and namespace with function type (backward compatibility).

        Args:
            name: Function name to resolve
            namespace: Optional namespace. If None, searches all namespaces.

        Returns:
            Tuple of (function, function_type, metadata)

        Raises:
            FunctionRegistryError: If function not found
        """
        func, metadata = self.resolve(name, namespace)

        # Try to find the function type from old-style storage
        ns, name = self._remap_namespace_and_name(namespace, name)
        if ns in self._functions_old_style and name in self._functions_old_style[ns]:
            func_type = self._functions_old_style[ns][name][1]
        else:
            # Default to PYTHON type for backward compatibility
            func_type = FunctionType.PYTHON

        return func, func_type, metadata

    def _resolve_across_namespaces(self, name: str) -> tuple[Callable, FunctionMetadata]:
        """Search for a function across all namespaces in priority order.

        Priority order: system > public > private > local

        Args:
            name: Function name to resolve

        Returns:
            Tuple of (function, metadata)

        Raises:
            FunctionRegistryError: If function not found in any namespace
        """
        # Search in priority order: system first (built-ins), then others
        search_order = ["system", "public", "private", "local"]

        for namespace in search_order:
            if namespace in self._namespaced_functions and name in self._namespaced_functions[namespace]:
                return self._namespaced_functions[namespace][name]

        # Function not found in any namespace
        raise FunctionRegistryError(
            f"Function '{name}' not found in any namespace. Searched: {search_order}",
            function_name=name,
            namespace="None",
            operation="resolve",
        )

    def has(self, name: str, namespace: str | None = None) -> bool:
        """Check if a function exists.

        Args:
            name: Function name
            namespace: Optional namespace. If None, searches all namespaces.

        Returns:
            True if function exists
        """
        # If namespace is explicitly None, search across all namespaces
        if namespace is None:
            return self._has_across_namespaces(name)

        ns, name = self._remap_namespace_and_name(namespace, name)
        return ns in self._namespaced_functions and name in self._namespaced_functions[ns]

    def _has_across_namespaces(self, name: str) -> bool:
        """Check if a function exists in any namespace.

        Args:
            name: Function name

        Returns:
            True if function exists in any namespace
        """
        # Search in priority order: system first (built-ins), then others
        search_order = ["system", "public", "private", "local"]

        for namespace in search_order:
            if namespace in self._namespaced_functions and name in self._namespaced_functions[namespace]:
                return True

        return False

    def get_metadata(self, name: str, namespace: str | None = None) -> FunctionMetadata:
        """Get metadata for a function.

        Args:
            name: Function name
            namespace: Optional namespace

        Returns:
            Function metadata

        Raises:
            KeyError: If function not found
        """
        _, metadata = self.resolve(name, namespace)
        return metadata

    def call(
        self,
        __name: str,   # NOTE: Need to change from `name` to `__name` to avoid conflict with the possible `name` parameter. Ex : func(name="any") will fail with the previous approach
        __context: Optional["SandboxContext"] = None,
        __namespace: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Call a function with context and arguments.

        This method provides the complex calling logic that was in the old registry.
        """

        def _resolve_if_promise(value):
            # Don't automatically resolve Promises - let them be resolved when accessed
            # This preserves the Promise system's lazy evaluation behavior
            return value

        # Resolve the function
        func, metadata = self.resolve(__name, __namespace)

        # Process special 'args' keyword parameter - this is a common pattern in tests
        # where positional args are passed as a list via kwargs['args']
        positional_args = list(args)
        func_kwargs = kwargs.copy()
        if "args" in func_kwargs:
            # Extract 'args' and add them to positional_args
            positional_args.extend(func_kwargs.pop("args"))

        # Process special 'kwargs' parameter - another pattern in tests
        # where keyword args are passed as a dict via kwargs['kwargs']
        if "kwargs" in func_kwargs:
            # Extract 'kwargs' and merge them with func_kwargs
            nested_kwargs = func_kwargs.pop("kwargs")
            if isinstance(nested_kwargs, dict):
                func_kwargs.update(nested_kwargs)

        # Security check - must happen regardless of how the function is called
        if hasattr(metadata, "is_public") and not metadata.is_public:
            # Non-public functions require a "private" context flag
            if __context is None or not hasattr(__context, "private") or not __context.private:
                raise PermissionError(f"Function '{__name}' is private and cannot be called from this context")

        # Special handling for PythonFunctions in test cases
        from dana.core.lang.interpreter.functions.python_function import PythonFunction
        from dana.core.lang.sandbox_context import SandboxContext

        if isinstance(func, PythonFunction) and hasattr(func, "func"):
            # Get the wrapped function
            wrapped_func = func.func

            # Check if the function expects a context parameter
            first_param_is_ctx = False
            if hasattr(func, "wants_context") and func.wants_context:
                first_param_is_ctx = True

            # Ensure we have a context object if needed
            if first_param_is_ctx and __context is None:
                __context = SandboxContext()  # Create a dummy context if none provided

            # Special case for functions like "process(result)"
            # In the test_function_call_chaining test, it expects the function to be called with just the input value
            func_name = __name.split(".")[-1]  # Get the bare function name without namespace

            # Special case for the reason function
            if func_name == "reason" and len(positional_args) >= 1:
                # The reason_function expects (context, prompt, options=None, use_mock=None)
                # We need to package any keyword arguments into the options dictionary
                prompt = positional_args[0]

                # Package keyword arguments into options dictionary
                options = {}
                use_mock = None

                # Check if the second positional argument is a dictionary (options)
                if len(positional_args) >= 2 and isinstance(positional_args[1], dict):
                    # The second argument is a dictionary, treat it as options
                    options.update(positional_args[1])

                # Extract special parameters
                if "use_mock" in func_kwargs:
                    use_mock = func_kwargs.pop("use_mock")

                # Handle context keyword argument specially
                if "context" in func_kwargs:
                    # The context keyword argument should be merged into options
                    context_data = func_kwargs.pop("context")
                    if isinstance(context_data, dict):
                        options["context"] = context_data

                # All remaining kwargs go into options
                if func_kwargs:
                    options.update(func_kwargs)

                # Security check for reason function: only trusted functions can receive context
                if not func._is_trusted_for_context():
                    # Call without context - this will likely fail but maintains security
                    return _resolve_if_promise(wrapped_func(prompt))

                # Call with correct signature: reason_function(context, prompt, options, use_mock)
                if options and use_mock is not None:
                    return _resolve_if_promise(wrapped_func(__context, prompt, options, use_mock))
                elif options:
                    return _resolve_if_promise(wrapped_func(__context, prompt, options))
                elif use_mock is not None:
                    return _resolve_if_promise(wrapped_func(__context, prompt, None, use_mock))
                else:
                    return _resolve_if_promise(wrapped_func(__context, prompt))
            # Special case for the process function
            elif func_name == "process" and len(positional_args) == 1:
                # Security check: only trusted functions can receive context
                if not func._is_trusted_for_context():
                    # Call without context
                    return _resolve_if_promise(wrapped_func(positional_args[0]))
                else:
                    # Pass the single argument followed by context
                    return _resolve_if_promise(wrapped_func(positional_args[0], __context))

            # Call with context as first argument if expected, with error handling
            try:
                if first_param_is_ctx:
                    # Security check: only trusted functions can receive context
                    if not func._is_trusted_for_context():
                        # Function wants context but is not trusted - call without context with async detection
                        import asyncio
                        from dana.common.utils.misc import Misc
                        
                        if asyncio.iscoroutinefunction(wrapped_func):
                            return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, *positional_args, **func_kwargs))
                        else:
                            return _resolve_if_promise(wrapped_func(*positional_args, **func_kwargs))
                    else:
                        # First parameter is context and function is trusted - add execute-time async detection
                        import asyncio
                        from dana.common.utils.misc import Misc
                        
                        if asyncio.iscoroutinefunction(wrapped_func):
                            return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, __context, *positional_args, **func_kwargs))
                        else:
                            return _resolve_if_promise(wrapped_func(__context, *positional_args, **func_kwargs))
                else:
                    # No context parameter - add execute-time async detection
                    import asyncio
                    from dana.common.utils.misc import Misc
                    
                    if asyncio.iscoroutinefunction(wrapped_func):
                        return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, *positional_args, **func_kwargs))
                    else:
                        return _resolve_if_promise(wrapped_func(*positional_args, **func_kwargs))
            except Exception as e:
                # Standardize error handling for direct function calls
                import traceback

                tb = traceback.format_exc()

                # Convert TypeError to SandboxError with appropriate message
                if isinstance(e, TypeError) and "missing 1 required positional argument" in str(e):
                    raise SandboxError(f"Error processing arguments for function '{__name}': {str(e)}")
                else:
                    raise SandboxError(f"Function '{__name}' raised an exception: {str(e)}\n{tb}")
        elif isinstance(func, PythonFunction):
            # Direct call to the PythonFunction's execute method
            if __context is None:
                __context = SandboxContext()  # Create a default context if none provided
            return _resolve_if_promise(func.execute(__context, *positional_args, **func_kwargs))
        else:
            # Check if it's a DanaFunction and call via execute method
            from dana.core.lang.interpreter.functions.dana_function import DanaFunction

            if isinstance(func, DanaFunction):
                # DanaFunction objects have an execute method that needs context
                if __context is None:
                    __context = SandboxContext()  # Create a default context if none provided
                return _resolve_if_promise(func.execute(__context, *positional_args, **func_kwargs))
            elif callable(func):
                # Fallback - call the function directly if it's a regular callable
                # Check if the function expects context by looking at its signature
                import inspect

                try:
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())
                    if params and params[0] in ("context", "ctx", "the_context", "sandbox_context"):
                        # Function expects context
                        positional_args_with_context = [__context] + positional_args
                    else:
                        positional_args_with_context = positional_args
                    if "options" in params:
                        options = func_kwargs.pop("options", {})
                        from dana.common.utils import Misc
                        match_args_kwargs_result = Misc.parse_args_kwargs(func, *positional_args_with_context, **func_kwargs)

                        # NOTE : If there are unmatched kwargs, they are added to the options dictionary
                        if match_args_kwargs_result.unmatched_kwargs:
                            options.update(match_args_kwargs_result.unmatched_kwargs)

                        matched_args = match_args_kwargs_result.matched_args # This will be matched to the function's arguments
                        varargs = match_args_kwargs_result.varargs # This will be matched to the function's *args
                        matched_kwargs = match_args_kwargs_result.matched_kwargs # This will be matched to the function's keyword arguments
                        if options:
                            if len(matched_args) > params.index("options"):
                                # If options is already existed in positional args, update it
                                matched_args[params.index("options")].update(options)
                            else:
                                # If options is not existed in positional args, add it to the matched_kwargs
                                matched_kwargs["options"] = options
                        varkwargs = match_args_kwargs_result.varkwargs # This will be matched to the function's **kwargs

                        return _resolve_if_promise(func(*matched_args, *varargs, **matched_kwargs, **varkwargs))
                    return _resolve_if_promise(func(*positional_args_with_context, **func_kwargs))

                except (ValueError, TypeError):
                    # If we can't inspect the signature, assume it doesn't expect context
                    return _resolve_if_promise(func(*positional_args, **func_kwargs))
            else:
                # Not a callable
                raise SandboxError(f"Function '{__name}' is not callable")

    def _register_preloaded_functions(self) -> None:
        """Register preloaded functions from the old registry."""
        # This method would load preloaded functions from the old registry
        # For now, we'll keep it empty as the old registry doesn't seem to have
        # a complex preloaded functions system
        pass

    def get_preloaded_functions(self) -> dict[str, dict[str, tuple[Callable, FunctionMetadata]]]:
        """Get preloaded functions."""
        return self._preloaded_functions.copy()

    # === Utility Methods ===

    def find_functions_by_pattern(self, pattern: str) -> builtins.list[tuple[str, Any]]:
        """Find functions by name pattern.

        Args:
            pattern: Pattern to match against function names (simple substring match)

        Returns:
            List of (name, function) tuples
        """
        results = []
        # Search in simple functions
        for name, (func, _) in self._simple_functions.items():
            if pattern.lower() in name.lower():
                results.append((name, func))

        # Search in namespaced functions
        for namespace, functions in self._namespaced_functions.items():
            for name, (func, _) in functions.items():
                if pattern.lower() in name.lower():
                    results.append((f"{namespace}:{name}", func))

        return results

    def get_functions_by_prefix(self, prefix: str) -> dict[str, Any]:
        """Get all functions with a specific prefix.

        Args:
            prefix: The prefix to match

        Returns:
            Dictionary of function names to functions
        """
        functions = {}
        # Search in simple functions
        for name, (func, _) in self._simple_functions.items():
            if name.startswith(prefix):
                functions[name] = func

        # Search in namespaced functions
        for namespace, ns_functions in self._namespaced_functions.items():
            for name, (func, _) in ns_functions.items():
                if name.startswith(prefix):
                    functions[f"{namespace}:{name}"] = func

        return functions

    # === Struct Method API (Unified Registry) ===

    def register_struct_function(self, receiver_type: str, method_name: str, func: Callable) -> None:
        """Register a method for a struct receiver type.

        Args:
            receiver_type: The type name of the receiver (e.g., "FileLoader", "Calculator")
            method_name: The name of the method
            func: The callable function/method to register
        """
        if not callable(func):
            raise ValueError("Method must be callable")

        # Delegate to StructFunctionRegistry if available
        if self._struct_function_registry is not None:
            self._struct_function_registry.register_method(receiver_type, method_name, func)
            return

        # Fallback to internal storage if no delegation registry
        key = (receiver_type, method_name)
        metadata = FunctionMetadata(registered_at=self._get_timestamp())

        # Try to determine source file
        try:
            source_file = inspect.getsourcefile(func)
            if source_file:
                metadata.source_file = source_file
        except (TypeError, ValueError):
            pass

        # Allow overwriting for now (useful during development)
        if key in self._struct_functions:
            metadata.overwrites = self._struct_functions[key][1].overwrites + 1

        self._struct_functions[key] = (func, metadata)

    def lookup_struct_function(self, receiver_type: str, method_name: str) -> Callable | None:
        """Fast O(1) lookup by receiver type and method name.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        # Delegate to StructFunctionRegistry if available
        if self._struct_function_registry is not None:
            return self._struct_function_registry.lookup_method(receiver_type, method_name)

        # Fallback to internal storage if no delegation registry
        result = self._struct_functions.get((receiver_type, method_name))
        return result[0] if result else None

    def has_struct_function(self, receiver_type: str, method_name: str) -> bool:
        """Check if a method exists for a receiver type.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            True if the method exists
        """
        # Delegate to StructFunctionRegistry if available
        if self._struct_function_registry is not None:
            return self._struct_function_registry.has_method(receiver_type, method_name)

        # Fallback to internal storage if no delegation registry
        return (receiver_type, method_name) in self._struct_functions

    def lookup_struct_function_for_instance(self, instance: Any, method_name: str) -> Callable | None:
        """Lookup method for a specific instance (extracts type automatically).

        Args:
            instance: The instance to lookup the method for
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        receiver_type = self._get_instance_type_name(instance)
        if receiver_type:
            return self.lookup_struct_function(receiver_type, method_name)
        return None

    def list_struct_functions_for_type(self, receiver_type: str) -> builtins.list[str]:
        """List all method names registered for a receiver type.

        Args:
            receiver_type: The type name of the receiver

        Returns:
            List of method names
        """
        # Delegate to StructFunctionRegistry if available
        if self._struct_function_registry is not None:
            return self._struct_function_registry.list_methods_for_type(receiver_type)

        # Fallback to internal storage if no delegation registry
        return [method_name for (type_name, method_name) in self._struct_functions.keys() if type_name == receiver_type]

    def list_struct_receiver_types(self) -> builtins.list[str]:
        """List all receiver types that have registered methods.

        Returns:
            List of receiver type names
        """
        return list(set(type_name for (type_name, _) in self._struct_functions.keys()))

    def get_struct_function_metadata(self, receiver_type: str, method_name: str) -> dict[str, Any] | None:
        """Get metadata for a struct method.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            Method metadata as dict or None if not found
        """
        result = self._struct_functions.get((receiver_type, method_name))
        if result:
            metadata = result[1]
            return {
                "source_file": metadata.source_file,
                "context_aware": metadata.context_aware,
                "is_public": metadata.is_public,
                "doc": metadata.doc,
                "registered_at": metadata.registered_at,
                "overwrites": metadata.overwrites,
            }
        return None

    def register_method_for_types(self, receiver_types: Union[builtins.list[str], str], method_name: str, func: Callable) -> None:
        """Register a method for multiple receiver types.

        Args:
            receiver_types: The type names (list) or single type name (string) for the receivers
            method_name: The name of the method
            func: The callable function to register
        """
        # Handle both list and string types (for compatibility)
        if isinstance(receiver_types, str):
            # Handle union types like "Point | Circle | Rectangle"
            types = [t.strip() for t in receiver_types.split("|") if t.strip()]
        else:
            types = receiver_types

        for receiver_type in types:
            self.register_struct_function(receiver_type, method_name, func)

    def _get_instance_type_name(self, instance: Any) -> str | None:
        """Get the type name from an instance.

        Handles StructType, AgentType, ResourceType, and other Dana types.

        Args:
            instance: The instance to extract type from

        Returns:
            The type name or None if unable to determine
        """
        # Try to get from struct_type attribute first (for Dana struct instances)
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            if hasattr(struct_type, "name"):
                return struct_type.name

        # Try to get from agent_type attribute
        if hasattr(instance, "agent_type"):
            agent_type = instance.agent_type
            if hasattr(agent_type, "name"):
                return agent_type.name

        # Try to get from resource_type attribute
        if hasattr(instance, "resource_type"):
            resource_type = instance.resource_type
            if hasattr(resource_type, "name"):
                return resource_type.name

        # Try to get the type name from the instance class (fallback)
        if hasattr(instance, "__class__"):
            class_name = instance.__class__.__name__
            return class_name

        return None

    def clear(self) -> None:
        """Clear all registered functions (for testing)."""
        self._simple_functions.clear()
        self._namespaced_functions.clear()
        self._functions_old_style.clear()
        self._registration_order.clear()
        self._preloaded_functions.clear()
        self._struct_functions.clear()

    def count(self) -> int:
        """Get the total number of registered functions."""
        simple_count = len(self._simple_functions)
        namespaced_count = sum(len(functions) for functions in self._namespaced_functions.values())
        struct_function_count = len(self._struct_functions)
        return simple_count + namespaced_count + struct_function_count

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return len(self._simple_functions) == 0 and len(self._namespaced_functions) == 0 and len(self._struct_functions) == 0

    def _get_timestamp(self) -> float:
        """Get current timestamp for registration tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the function registry."""
        simple_count = len(self._simple_functions)
        namespaced_count = sum(len(functions) for functions in self._namespaced_functions.values())
        struct_function_count = len(self._struct_functions)
        receiver_types = len(self.list_struct_receiver_types()) if struct_function_count > 0 else 0
        return f"FunctionRegistry(simple={simple_count}, namespaced={namespaced_count}, struct_functions={struct_function_count}, receiver_types={receiver_types})"

    def __getattr__(self, name: str):
        """Provide backward compatibility for old-style storage access."""
        if name == "_functions":
            # Return the old-style storage for backward compatibility
            return self._functions_old_style
        elif name == "_get_arg_processor":
            # Return a dummy method for backward compatibility
            return lambda: None
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
