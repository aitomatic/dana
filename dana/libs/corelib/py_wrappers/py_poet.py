"""
POET Function for Dana standard library.

This module provides a Dana function that allows users to apply POET enhancements
to any function call directly from Dana code.
"""

__all__ = ["py_poet", "py_apply_poet", "py_poet_decorator", "py_poet_call"]

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.frameworks.poet import POETConfig


def py_poet(
    context: SandboxContext,
    domain: str | None = None,
    **kwargs,
) -> Any:
    """
    POET decorator for Dana functions.

    This function creates a decorator that can be used with the @poet syntax.
    It wraps the actual poet decorator from the frameworks module.

    Args:
        context: The sandbox context (automatically injected)
        domain: Domain specialization
        **kwargs: Additional configuration options

    Returns:
        A decorator function that enhances Dana functions with POET capabilities
    """
    # Import the actual decorator from the frameworks module
    from dana.frameworks.poet.core.decorator import poet

    # Create the decorator with the provided arguments
    decorator = poet(domain=domain, **kwargs)

    # Return the decorator (it will be called with the function to decorate)
    return decorator


def py_poet_decorator(
    context: SandboxContext,
    domain: str | None = None,
    **kwargs,
) -> Any:
    """
    POET decorator factory for Dana functions.

    This function creates a decorator that can be used with the @poet syntax.
    It wraps the actual poet decorator from the frameworks module.

    Args:
        context: The sandbox context (automatically injected)
        domain: Domain specialization
        **kwargs: Additional configuration options

    Returns:
        A decorator function that enhances Dana functions with POET capabilities
    """
    # Import the actual decorator from the frameworks module
    from dana.frameworks.poet.core.decorator import poet

    # Create the decorator with the provided arguments
    decorator = poet(domain=domain, **kwargs)

    # Return the decorator (it will be called with the function to decorate)
    return decorator


def py_poet_call(
    context: SandboxContext,
    func_name: str,
    args: list | None = None,
    kwargs: dict[str, Any] | None = None,
    domain: str | None = None,
    timeout: float | None = None,
    retries: int | None = None,
    enable_training: bool = True,
    enable_monitoring: bool = True,
) -> Any:
    """
    Apply POET enhancements to any function call.

    This function allows Dana code to leverage POET's Perceive-Operate-Enforce
    pipeline for enhanced reliability, performance, and domain expertise.

    Args:
        context: The sandbox context (automatically injected)
        func_name: Name of the function to call with POET enhancements
        args: Positional arguments for the function (optional)
        kwargs: Keyword arguments for the function (optional)
        domain: Domain specialization (optional)
        timeout: Maximum execution time in seconds (optional)
        retries: Number of retry attempts (optional)
        enable_training: Whether to enable learning from execution (default: True)

    Returns:
        The function result enhanced through POET processing

    Example (in Dana):
        # Basic POET enhancement
        result = poet("reason", ["Analyze this data"], {"temperature": 0.7})

        # With domain specialization
        result = poet("calculate_risk", [portfolio], domain="financial_services")

        # With custom timeout and retries
        result = poet("complex_analysis", [data], timeout=30.0, retries=3)
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    # Create POET configuration
    POETConfig(
        domain=domain,
        timeout=timeout or 30.0,
        retries=retries or 2,
        enable_training=enable_training,
    )

    # Look up the function in the registry
    interpreter = context.get_interpreter()
    if not interpreter:
        raise RuntimeError("Interpreter not available in context")

    registry = interpreter.function_registry

    # Resolve the original function
    original_func, func_type, metadata = registry.resolve_with_type(func_name)

    # TODO: Create POET executor and wrap the function (Alpha: deferred)
    # poe_executor = POETExecutor(config)

    # Create a wrapper function that will be enhanced by POE
    def target_function(*call_args, **call_kwargs):
        return registry.call(func_name, context, None, *call_args, **call_kwargs)

    # TODO: Apply POET enhancement to the wrapper (Alpha: deferred)
    # enhanced_function = poe_executor(target_function)
    enhanced_function = target_function

    # Call the enhanced function with the provided arguments
    return enhanced_function(*args, **kwargs)


def py_apply_poet(
    context: SandboxContext,
    operation: Any,
    config: dict[str, Any] | None = None,
) -> Any:
    """
    Apply POET enhancements to a callable operation.

    This is a lower-level function that allows applying POET to any callable,
    not just registered Dana functions.

    Args:
        context: The sandbox context (automatically injected)
        operation: The callable operation to enhance
        config: POET configuration options

    Returns:
        The operation result enhanced through POET processing
    """
    if config is None:
        config = {}

    # Create POET configuration from provided options
    POETConfig(
        domain=config.get("domain"),
        timeout=config.get("timeout", 30.0),
        retries=config.get("retries", 2),
        enable_training=config.get("enable_training", True),
    )

    # TODO: Create POET executor and apply enhancement (Alpha: deferred)
    # poe_executor = POETExecutor(poe_config)
    # enhanced_operation = poe_executor(operation)
    enhanced_operation = operation

    # Call the enhanced operation
    return enhanced_operation()
