"""Registry for Python functions that can be called from DANA code.

This module provides a registry for Python functions that can be called from DANA code.
Functions can be registered by name and called with arguments.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from opendxa.dana.common.exceptions import SandboxError, StateError
from opendxa.dana.common.runtime_scopes import RuntimeScopes

# Type for function implementations
FunctionImpl = Callable[[Dict[str, Any]], Any]


class PythonRegistry:
    """Registry for Python functions that can be called from DANA code.

    This registry manages Python functions that are exposed to DANA code.
    Functions are registered by name and can be called with arguments.
    Each function implementation receives a dictionary of argument values.
    """

    # Singleton instance
    _instance: Optional["PythonRegistry"] = None

    def __init__(self):
        """Initialize an empty function registry."""
        self._functions: Dict[str, Tuple[FunctionImpl, Dict[str, Any]]] = {}

    @classmethod
    def get_instance(cls) -> "PythonRegistry":
        """Get the singleton instance of the function registry.

        Returns:
            The singleton PythonFunctionRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._register_standard_functions()
        return cls._instance

    def _register(self, name: str, func: FunctionImpl, metadata: Optional[Dict[str, Any]] = None) -> None:
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

    def _unregister(self, name: str) -> None:
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

    def _call(self, name: str, args: Dict[str, Any]) -> Any:
        """Call a function by name with the given arguments.

        Args:
            name: The name of the function to call
            args: The arguments to pass to the function

        Returns:
            The result of calling the function

        Raises:
            StateError: If the function is not registered
            RuntimeError: If the function raises an exception
        """
        try:
            func, _ = self.get(name)
            return func(args)
        except StateError:
            raise
        except Exception as e:
            raise SandboxError(f"Error calling function '{name}': {str(e)}") from e

    def _list(self) -> List[str]:
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

    def _has(self, name: str) -> bool:
        """Check if a function is registered with the given name.

        Args:
            name: The name of the function to check

        Returns:
            True if the function is registered, False otherwise
        """
        return name in self._functions

    @classmethod
    def register(cls, name: str, func: FunctionImpl, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a Python function with the global registry.

        Args:
            name: The name to register the function under
            func: The Python function implementation to register
            metadata: Optional metadata about the function
        """
        cls.get_instance()._register(name, func, metadata)

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a Python function from the global registry.

        Args:
            name: The name of the function to unregister
        """
        cls.get_instance()._unregister(name)

    @classmethod
    def call(cls, name: str, args: Dict[str, Any]) -> Any:
        """Call a registered Python function from the global registry.

        This function calls out to a Python function that was previously registered.
        The function receives a dictionary of arguments.

        Args:
            name: The name of the registered Python function to call
            args: Dictionary of arguments to pass to the function

        Returns:
            The result of calling the Python function

        Raises:
            StateError: If no function is registered with the given name
        """
        return cls.get_instance()._call(name, args)

    @classmethod
    def list(cls) -> List[str]:
        """List all Python functions in the global registry.

        Returns:
            A list of all registered function names
        """
        return cls.get_instance()._list()

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a Python function exists in the global registry.

        Args:
            name: The name of the function to check

        Returns:
            True if the function exists, False otherwise
        """
        return cls.get_instance()._has(name)

    @staticmethod
    def _log_function(args: Dict[str, Any]) -> None:
        """Standard log function implementation."""
        if "message" not in args:
            raise ValueError("Log function requires a 'message' argument")

        message = args["message"]
        level = args.get("level", "INFO").upper()

        # Use DXA_LOGGER directly
        from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER

        DXA_LOGGER.log(level, str(message))

        return None

    @staticmethod
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

    @staticmethod
    def _reason2_function(args: Dict[str, Any]) -> Any:
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
        context_vars, special_args = PythonRegistry._parse_context_vars(args)

        # Handle positional arguments if present
        if "__positional" in special_args and special_args["__positional"]:
            prompt = special_args["__positional"][0]  # First positional arg is prompt
        elif "prompt" in special_args:
            prompt = special_args["prompt"]
        else:
            raise ValueError("reason2 function requires a 'prompt' argument")

        # Get options (only temperature and format)
        options = {}
        if "temperature" in special_args:
            options["temperature"] = special_args["temperature"]
        if "format" in special_args:
            options["format"] = special_args["format"]

        # Get the LLM integration from the context
        try:
            llm_integration = args.get("llm_integration")
            if not llm_integration:
                raise SandboxError("No LLM integration available")
        except StateError:
            raise SandboxError("No LLM integration available")

        # Execute the reasoning with the augmented context
        result = llm_integration.execute_direct_synchronous_reasoning(prompt, context_vars=None, options=options if options else None)

        return result

    @classmethod
    def _register_standard_functions(cls) -> None:
        """Register standard functions with the global registry."""
        cls.register(
            "log2",
            cls._log_function,
            {
                "description": "Log a message with the given level",
                "parameters": {
                    "message": {"type": "string", "description": "The message to log"},
                    "level": {"type": "string", "description": "The log level (DEBUG, INFO, WARN, ERROR)", "default": "INFO"},
                },
            },
        )

        cls.register(
            "reason2",
            cls._reason2_function,
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


# Initialize the registry with standard functions when the module is loaded
PythonRegistry.get_instance()
