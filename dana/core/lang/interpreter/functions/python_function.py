"""Python function."""

import inspect
import logging
from collections.abc import Callable
from typing import Any

from dana.core.lang.sandbox_context import SandboxContext

from .sandbox_function import SandboxFunction


class PythonFunction(SandboxFunction):
    """Wrapper for Python functions that makes them compatible with BaseFunction interface."""

    def __init__(self, func: Callable, context: SandboxContext | None = None, trusted_for_context: bool = False):
        """Initialize a Python function wrapper.

        Args:
            func: The Python function to wrap
            context: Optional sandbox context
            trusted_for_context: Whether this function is trusted to receive SandboxContext
        """
        super().__init__(context)
        self.func = func
        self.wants_context = False
        self.context_param_name = None
        self.trusted_for_context = trusted_for_context  # Explicit trust flag

        # Extract parameters from function signature
        self.parameters: list[str] = []  # All parameters
        self.required_parameters: set[str] = set()  # Required parameters (no default)
        self.defaults: dict[str, Any] = {}  # Default values for parameters

        # Special parameters that are not exposed to argument binding
        self.special_params: set[str] = set()

        try:
            sig = inspect.signature(func)
            param_names = []
            required_params = set()
            default_values = {}

            # Get all parameters and identify which are required
            for name, param in sig.parameters.items():
                # Check if this parameter is a context parameter by name or annotation
                if self._is_context_parameter(name, param):
                    self.wants_context = True
                    self.context_param_name = name
                    self.special_params.add(name)
                    continue

                # Add to parameter list
                param_names.append(name)

                # If parameter has a default, store it
                if param.default is not param.empty:
                    default_values[name] = param.default
                # If parameter has no default and isn't VAR_POSITIONAL or VAR_KEYWORD,
                # it's required
                elif param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    required_params.add(name)

            self.parameters = param_names
            self.required_parameters = required_params
            self.defaults = default_values

        except (ValueError, TypeError):
            # If we can't get parameters, use empty collections
            self.parameters = []
            self.required_parameters = set()
            self.defaults = {}

    def _is_context_parameter(self, name: str, param: inspect.Parameter) -> bool:
        """
        Determine if a parameter is a context parameter.

        A parameter is considered a context parameter if:
        1. It has a name like "context", "ctx", etc.
        2. It has a type annotation matching SandboxContext

        Args:
            name: Parameter name
            param: Parameter object

        Returns:
            True if this is a context parameter
        """
        # Check by name
        if name in ("ctx", "context", "the_context", "sandbox_context"):
            return True

        # Check by annotation if available
        try:
            if param.annotation != param.empty:
                # Get the annotation as a string and check if it matches SandboxContext
                anno_str = str(param.annotation)
                if "SandboxContext" in anno_str:
                    return True

                # Also check for 'context' in the type name (for custom context classes)
                if "context" in anno_str.lower() or "ctx" in anno_str.lower():
                    return True
        except Exception:
            # Ignore errors in annotation checking
            pass

        return False

    def _is_trusted_for_context(self) -> bool:
        """
        Security check: Determine if this function is trusted to receive SandboxContext.

        This uses an explicit trust flag set during registration.

        Returns:
            True if the function is trusted to receive SandboxContext
        """
        return self.trusted_for_context

    def prepare_context(self, context: SandboxContext, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a Python function.

        For Python functions:
        - Creates a sanitized context for safety
        - No need to map arguments to context (will be passed directly)

        Args:
            context: The original context
            args: Positional arguments (ignored for Python functions)
            kwargs: Keyword arguments (ignored for Python functions)

        Returns:
            Sanitized context
        """
        # For Python functions, we just sanitize the context
        return context.copy().sanitize()

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """
        Restore the context after Python function execution.

        For Python functions, there's typically no need to restore context
        since they don't modify it directly (changes happen via return values).

        Args:
            context: The current context
            original_context: The original context before execution
        """
        # No restoration needed for Python functions
        pass

    def inject_context(self, context: SandboxContext, kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Handle context injection for Python functions that want it.

        Args:
            context: The context to inject
            kwargs: The existing keyword arguments

        Returns:
            Updated keyword arguments with context injected if needed
        """
        # Check if the function wants context and has a parameter name for it
        if self.wants_context and self.context_param_name:
            # If parameter name already exists in kwargs, log a warning but don't override
            param_name = self.context_param_name
            if param_name in kwargs:
                # Don't override existing value, but log a warning
                logger = logging.getLogger(__name__)
                logger.warning(f"Context parameter '{param_name}' already exists in kwargs. Not injecting context automatically.")
            else:
                # Inject the context parameter
                kwargs[param_name] = context

        return kwargs

    def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
        """Execute the function body with the provided context and arguments.

        Args:
            context: The context to use for execution
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of calling the Python function
        """
        import asyncio
        from dana.common.utils.misc import Misc

        # Security check: only trusted functions can receive context
        if self.wants_context and self.context_param_name:
            if not self._is_trusted_for_context():
                # Function wants context but is not trusted - call without context
                if asyncio.iscoroutinefunction(self.func):
                    return Misc.safe_asyncio_run(self.func, *args, **kwargs)
                else:
                    return self.func(*args, **kwargs)

            # Function is trusted - proceed with context injection
            try:
                sig = inspect.signature(self.func)
                param_names = list(sig.parameters.keys())
                if param_names and param_names[0] == self.context_param_name:
                    # Context is first parameter - pass as positional argument
                    # Remove context from kwargs if it was injected there
                    kwargs.pop(self.context_param_name, None)
                    if asyncio.iscoroutinefunction(self.func):
                        return Misc.safe_asyncio_run(self.func, context, *args, **kwargs)
                    else:
                        return self.func(context, *args, **kwargs)
                else:
                    # Context is not first parameter - inject it into kwargs
                    kwargs = self.inject_context(context, kwargs)
                    if asyncio.iscoroutinefunction(self.func):
                        return Misc.safe_asyncio_run(self.func, *args, **kwargs)
                    else:
                        return self.func(*args, **kwargs)
            except (AttributeError, OSError):
                # Fallback to using kwargs with context injection
                kwargs = self.inject_context(context, kwargs)
                if asyncio.iscoroutinefunction(self.func):
                    return Misc.safe_asyncio_run(self.func, *args, **kwargs)
                else:
                    return self.func(*args, **kwargs)
        else:
            # Function doesn't want context - call normally with async detection
            if asyncio.iscoroutinefunction(self.func):
                return Misc.safe_asyncio_run(self.func, *args, **kwargs)
            else:
                return self.func(*args, **kwargs)
