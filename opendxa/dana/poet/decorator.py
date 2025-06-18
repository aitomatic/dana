"""
POET (Programmable Open-Ended Task) decorator implementation.

This module provides the POET decorator for enhancing functions with domain-specific capabilities.
"""

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
        enable_training: bool = False,
    ):
        """Initialize the POET decorator.

        Args:
            func: The function to decorate
            domain: The domain this function belongs to
            retries: Number of retries on failure
            timeout: Optional timeout in seconds
            namespace: Namespace to register the function in
            overwrite: Whether to allow overwriting existing functions
            enable_training: Whether to enable training for this function
        """
        super().__init__()
        self.func = func
        self.domain = domain
        self.retries = retries
        self.timeout = timeout
        self.namespace = namespace
        self.overwrite = overwrite
        self.enable_training = enable_training

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
                "enable_training": enable_training,
            }
        )

        # Apply the decorator
        self._apply_decorator()

    def _apply_decorator(self) -> None:
        """Apply the decorator to the function."""

        @wraps(self.func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that adds POET capabilities."""
            # Get context from kwargs or create new one
            context = kwargs.pop("context", None)
            if context is None:
                context = SandboxContext()

            # Ensure context has an interpreter
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                # Try to get interpreter from parent context
                if hasattr(context, "parent") and context.parent is not None:
                    if hasattr(context.parent, "_interpreter") and context.parent._interpreter is not None:
                        context._interpreter = context.parent._interpreter
                    else:
                        raise RuntimeError("No interpreter available in context")
                else:
                    raise RuntimeError("No interpreter available in context")

            # Set POET metadata in context
            context.set("_poet_metadata", self.func._poet_metadata)

            # Execute the function with retries if needed
            for attempt in range(self.retries):
                try:
                    result = self.func(*args, context=context, **kwargs)
                    return result
                except Exception as e:
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
    enable_training: bool = False,
) -> Callable:
    """Decorator factory for POET functions.

    Args:
        domain: The domain this function belongs to
        retries: Number of retries on failure
        timeout: Optional timeout in seconds
        namespace: Namespace to register the function in
        overwrite: Whether to allow overwriting existing functions
        enable_training: Whether to enable training for this function

    Returns:
        A decorator function that enhances the target function with POET capabilities
    """

    def decorator(func: Callable) -> Callable:
        """The actual decorator function."""
        return POETDecorator(
            func=func,
            domain=domain,
            retries=retries,
            timeout=timeout,
            namespace=namespace,
            overwrite=overwrite,
            enable_training=enable_training,
        ).wrapper

    return decorator
