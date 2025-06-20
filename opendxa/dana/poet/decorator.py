"""
POET (Programmable Open-Ended Task) decorator implementation.

This module provides the POET decorator for enhancing functions with domain-specific capabilities.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.sandbox_context import SandboxContext


# Minimal stub for POETMetadata to fix test import error
class POETMetadata:
    pass


class POETDecorator(Loggable):
    """Decorator for enhancing functions with POET capabilities."""

    def __init__(
        self,
        func: Callable,
        domain: str,
        retries: int = 1,
        timeout: int | None = None,
        namespace: str = "local",
        overwrite: bool = False,
        optimize_for: str | None = None,
    ):
        """Initialize the POET decorator.

        Args:
            func: The function to decorate
            domain: The domain this function belongs to
            retries: Number of retries on failure
            timeout: Optional timeout in seconds
            namespace: Namespace to register the function in
            overwrite: Whether to allow overwriting existing functions
            optimize_for: Optional optimization target for learning (enables training when specified)
        """
        super().__init__()
        self.func = func
        self.domain = domain
        self.retries = retries
        self.timeout = timeout
        self.namespace = namespace
        self.overwrite = overwrite
        self.optimize_for = optimize_for

        # Store metadata on the function
        if not hasattr(func, "_poet_metadata"):
            setattr(func, "_poet_metadata", {"domains": set()})
        func._poet_metadata["domains"].add(domain)
        func._poet_metadata.update(
            {
                "retries": retries,
                "timeout": timeout,
                "namespace": namespace,
                "overwrite": overwrite,
                "optimize_for": optimize_for,
            }
        )

        # Apply the decorator
        self._apply_decorator()

    def _apply_decorator(self) -> None:
        """Apply the decorator to the function."""
        # Check if the function is a DanaFunction or expects context as first parameter
        is_dana_function = hasattr(self.func, "execute") and hasattr(self.func, "parameters")

        if not is_dana_function:
            # For regular Python functions, check if they expect a context parameter
            sig = inspect.signature(self.func)
            expects_context = "context" in sig.parameters

        @wraps(self.func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that adds POET capabilities."""
            # DEBUG: Log all inputs to understand what's being passed
            DXA_LOGGER.debug(f"POET wrapper called with args={args}, kwargs={kwargs}")

            # Get context from kwargs or create new one
            context = kwargs.pop("context", None)

            DXA_LOGGER.debug(f"POET wrapper context from kwargs: {context}")
            DXA_LOGGER.debug(f"Context type: {type(context)}")
            if context is not None:
                DXA_LOGGER.debug(f"Context has _interpreter: {hasattr(context, '_interpreter')}")
                if hasattr(context, "_interpreter"):
                    DXA_LOGGER.debug(f"Context _interpreter value: {context._interpreter}")

            if context is None:
                context = SandboxContext()
                DXA_LOGGER.debug("Created new SandboxContext")

            # CRITICAL: Ensure context has an interpreter reference
            # This is essential for Dana function execution
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                DXA_LOGGER.debug("Context missing interpreter - attempting to find one")
                # Try to get interpreter from:
                # 1. Parent context if available
                if hasattr(context, "parent") and context.parent is not None:
                    if hasattr(context.parent, "_interpreter") and context.parent._interpreter is not None:
                        context._interpreter = context.parent._interpreter
                        DXA_LOGGER.debug("Inherited interpreter from parent context")
                    else:
                        DXA_LOGGER.warning("Parent context found but no interpreter available")
                else:
                    # 2. Try to get from the current execution stack
                    # When Dana functions are called through the function registry,
                    # there should be an interpreter in the call stack
                    try:
                        import inspect

                        for frame_info in inspect.stack():
                            frame_locals = frame_info.frame.f_locals
                            if "_interpreter" in frame_locals:
                                context._interpreter = frame_locals["_interpreter"]
                                DXA_LOGGER.debug("Found interpreter in call stack")
                                break
                            elif "self" in frame_locals and hasattr(frame_locals["self"], "_interpreter"):
                                context._interpreter = frame_locals["self"]._interpreter
                                DXA_LOGGER.debug("Found interpreter via self in call stack")
                                break
                        else:
                            DXA_LOGGER.warning("No interpreter found in call stack for POET function")
                    except Exception as e:
                        DXA_LOGGER.debug(f"Error searching for interpreter in call stack: {e}")
            else:
                DXA_LOGGER.debug("Context already has interpreter")

            # Set POET metadata in context
            context.set("_poet_metadata", self.func._poet_metadata)

            # Execute the function with retries if needed
            for attempt in range(self.retries):
                try:
                    DXA_LOGGER.debug(f"POET executing function (attempt {attempt + 1})")
                    if is_dana_function:
                        # Dana function - call execute method with context as first argument
                        DXA_LOGGER.debug(f"Calling Dana function.execute with context={context}")
                        result = self.func.execute(context, *args, **kwargs)
                    elif not is_dana_function and expects_context:
                        # Regular Python function that expects context parameter
                        # Check if context is already provided as a positional argument
                        sig = inspect.signature(self.func)
                        param_names = list(sig.parameters.keys())

                        if len(args) > 0 and len(param_names) > 0 and param_names[0] == "context":
                            # Context is likely already the first positional argument
                            result = self.func(*args, **kwargs)
                        else:
                            # Context needs to be passed as keyword argument
                            result = self.func(*args, context=context, **kwargs)
                    else:
                        # Regular Python function that doesn't expect context
                        result = self.func(*args, **kwargs)
                    DXA_LOGGER.debug(f"POET function completed with result: {result}")
                    return result
                except Exception as e:
                    DXA_LOGGER.error(f"POET function failed on attempt {attempt + 1}: {e}")
                    if attempt == self.retries - 1:
                        raise
                    DXA_LOGGER.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        # Store the wrapper
        self.wrapper = wrapper


def poet(
    domain: str,
    retries: int = 1,
    timeout: int | None = None,
    namespace: str = "local",
    overwrite: bool = False,
    optimize_for: str | None = None,
) -> Callable:
    """Decorator factory for POET functions.

    Args:
        domain: The domain this function belongs to
        retries: Number of retries on failure
        timeout: Optional timeout in seconds
        namespace: Namespace to register the function in
        overwrite: Whether to allow overwriting existing functions
        optimize_for: Optional optimization target for learning (enables training when specified)

    Returns:
        A decorator function that enhances the target function with POET capabilities
    """

    def decorator(func: Callable) -> Callable:
        """The actual decorator function."""
        poet_decorator = POETDecorator(
            func=func,
            domain=domain,
            retries=retries,
            timeout=timeout,
            namespace=namespace,
            overwrite=overwrite,
            optimize_for=optimize_for,
        )
        return poet_decorator.wrapper

    return decorator
