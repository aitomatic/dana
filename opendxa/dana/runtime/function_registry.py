"""Function registry for DANA runtime.

This module provides a registry for functions that can be called from DANA code.
Functions can be registered by name and called with arguments.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.exceptions import RuntimeError, StateError
from opendxa.dana.runtime.context import RuntimeContext

# Type for function implementations
FunctionImpl = Callable[[RuntimeContext, Dict[str, Any]], Any]


class FunctionRegistry:
    """Registry for functions that can be called from DANA code.

    Functions are registered by name and can be called with arguments.
    Each function implementation receives the runtime context and argument values.
    """

    def __init__(self):
        """Initialize an empty function registry."""
        self._functions: Dict[str, Tuple[FunctionImpl, Dict[str, Any]]] = {}

    def register(self, name: str, func: FunctionImpl, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a function with the given name.

        Args:
            name: The name to register the function under
            func: The function implementation to register
            metadata: Optional metadata about the function (e.g., description, parameter types)

        Raises:
            ValueError: If the name is empty or the function is None
        """
        if not name:
            raise ValueError("Function name cannot be empty")
        if func is None:
            raise ValueError("Function implementation cannot be None")

        self._functions[name] = (func, metadata or {})

    def unregister(self, name: str) -> None:
        """Unregister a function with the given name.

        Args:
            name: The name of the function to unregister

        Raises:
            KeyError: If the function is not registered
        """
        if name not in self._functions:
            raise KeyError(f"Function '{name}' is not registered")

        del self._functions[name]

    def get(self, name: str) -> Tuple[FunctionImpl, Dict[str, Any]]:
        """Get a function by name.

        Args:
            name: The name of the function to get

        Returns:
            A tuple containing the function implementation and metadata

        Raises:
            StateError: If the function is not registered
        """
        if name not in self._functions:
            raise StateError(f"Function '{name}' is not registered")

        return self._functions[name]

    def call(self, name: str, context: RuntimeContext, args: Dict[str, Any]) -> Any:
        """Call a function by name with the given arguments.

        Args:
            name: The name of the function to call
            context: The runtime context to pass to the function
            args: The arguments to pass to the function

        Returns:
            The result of calling the function

        Raises:
            StateError: If the function is not registered
            RuntimeError: If the function raises an exception
        """
        try:
            func, _ = self.get(name)
            return func(context, args)
        except StateError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error calling function '{name}': {str(e)}") from e

    def list(self) -> List[str]:
        """List all registered function names.

        Returns:
            A list of all registered function names
        """
        return list(self._functions.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a function by name.

        Args:
            name: The name of the function to get metadata for

        Returns:
            The metadata for the function

        Raises:
            StateError: If the function is not registered
        """
        if name not in self._functions:
            raise StateError(f"Function '{name}' is not registered")

        return self._functions[name][1]

    def has_function(self, name: str) -> bool:
        """Check if a function is registered with the given name.

        Args:
            name: The name of the function to check

        Returns:
            True if the function is registered, False otherwise
        """
        return name in self._functions


# Singleton instance for the function registry
_registry = FunctionRegistry()


def get_registry() -> FunctionRegistry:
    """Get the global function registry instance.

    Returns:
        The global FunctionRegistry instance
    """
    return _registry


# Convenience functions for working with the global registry


def register_function(name: str, func: FunctionImpl, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Register a function with the global registry.

    Args:
        name: The name to register the function under
        func: The function implementation to register
        metadata: Optional metadata about the function
    """
    _registry.register(name, func, metadata)


def unregister_function(name: str) -> None:
    """Unregister a function from the global registry.

    Args:
        name: The name of the function to unregister
    """
    _registry.unregister(name)


def call_function(name: str, context: RuntimeContext, args: Dict[str, Any]) -> Any:
    """Call a function from the global registry.

    Args:
        name: The name of the function to call
        context: The runtime context to pass to the function
        args: The arguments to pass to the function

    Returns:
        The result of calling the function
    """
    return _registry.call(name, context, args)


def list_functions() -> List[str]:
    """List all functions in the global registry.

    Returns:
        A list of all registered function names
    """
    return _registry.list()


def has_function(name: str) -> bool:
    """Check if a function exists in the global registry.

    Args:
        name: The name of the function to check

    Returns:
        True if the function exists, False otherwise
    """
    return _registry.has_function(name)


# Register standard functions


def _log_function(context: RuntimeContext, args: Dict[str, Any]) -> None:
    """Standard log function implementation."""
    if "message" not in args:
        raise ValueError("Log function requires a 'message' argument")

    message = args["message"]
    level = args.get("level", "INFO").upper()

    # Use DXA_LOGGER directly
    from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER

    DXA_LOGGER.log(level, str(message))

    return None


def _parse_context_vars(kwargs: Dict[str, Any], special_keys: Optional[List[str]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse context variables from kwargs, separating them from special arguments.

    This utility function processes kwargs to extract context variables and special arguments.
    Context variables are any named arguments that are not in the special_keys list.
    Unscoped variables are treated as private variables.

    Args:
        kwargs: Dictionary of keyword arguments to process
        special_keys: List of keys to treat as special arguments (not context variables)
                     Defaults to ["prompt", "__positional", "temperature", "format"]

    Returns:
        Tuple containing:
        - Dictionary of context variables with proper scoping
        - Dictionary of special arguments

    Raises:
        ValueError: If any system variables are found in the context variables
    """
    if special_keys is None:
        special_keys = ["prompt", "__positional", "temperature", "format"]

    context_vars = {}
    special_args = {}

    for key, value in kwargs.items():
        if key in special_keys:
            special_args[key] = value
            continue

        # Check if key is a system variable (not allowed)
        if key.startswith("system."):
            raise ValueError(f"System variables are not allowed in context: {key}")

        # If key is unscoped, treat it as local
        if "." in key and not any(key.startswith(scope) for scope in RuntimeScopes.ALL_WITH_DOT):
            scoped_key = f"local.{key}"
        else:
            scoped_key = key

        context_vars[scoped_key] = value

    return context_vars, special_args


def _reason2_function(context: RuntimeContext, args: Dict[str, Any]) -> Any:
    """Alternative implementation of reason as a registered function.

    This function provides similar functionality to the reason statement
    but implemented as a regular function.

    Args can be provided in two ways:
    1. Named arguments: {"prompt": "...", "var1": "value1", "var2": "value2", ...}
    2. Positional arguments: {"__positional": ["prompt value", ...], "var1": "value1", ...}

    All named arguments (except prompt and special options) are treated as context variables
    that augment a local copy of the RuntimeContext:
    - Unscoped variables (e.g., "var") are treated as "private.var"
    - Scoped variables (e.g., "private.var" or "public.var") are used as is
    - System variables (e.g., "system.var") are not allowed

    Special arguments:
    - prompt: The reasoning prompt (required)
    - temperature: Optional LLM temperature parameter
    - format: Optional output format (text/json)
    """
    # Parse context variables and special arguments
    context_vars, special_args = _parse_context_vars(args)

    # Handle positional arguments if present
    if "__positional" in special_args and special_args["__positional"]:
        prompt = special_args["__positional"][0]  # First positional arg is prompt
    elif "prompt" in special_args:
        prompt = special_args["prompt"]
    else:
        raise ValueError("reason2 function requires a 'prompt' argument")

    # Create a local copy of the RuntimeContext
    local_context = RuntimeContext.from_dict({}, context)

    # Add context variables to local context
    for key, value in context_vars.items():
        local_context.set(key, value)

    # Get options (only temperature and format)
    options = {}
    if "temperature" in special_args:
        options["temperature"] = special_args["temperature"]
    if "format" in special_args:
        options["format"] = special_args["format"]

    # Get the LLM integration from the context
    try:
        llm_integration = local_context.get_resource("llm_integration")
        if not llm_integration:
            raise RuntimeError("No LLM integration available")
    except StateError:
        raise RuntimeError("No LLM integration available")

    # Execute the reasoning with the augmented context
    result = llm_integration.execute_direct_synchronous_reasoning(prompt, context_vars=None, options=options if options else None)

    return result


def _register_standard_functions() -> None:
    """Register standard functions with the global registry."""
    register_function(
        "log",
        _log_function,
        {
            "description": "Log a message with the given level",
            "parameters": {
                "message": {"type": "string", "description": "The message to log"},
                "level": {"type": "string", "description": "The log level (DEBUG, INFO, WARN, ERROR)", "default": "INFO"},
            },
        },
    )

    register_function(
        "reason2",
        _reason2_function,
        {
            "description": "Alternative implementation of reason as a function",
            "parameters": {
                "prompt": {"type": "string", "description": "The reasoning prompt"},
                "context": {"type": "string|list", "description": "Optional context variables to include", "optional": True},
                "temperature": {"type": "number", "description": "LLM temperature parameter", "optional": True},
                "format": {"type": "string", "description": "Output format (text/json)", "optional": True},
            },
        },
    )

    # Add other standard functions here


# Register standard functions when the module is imported
_register_standard_functions()
