"""
POET Function for Dana

This module provides a Dana function that allows users to apply POET enhancements
to any function call directly from Dana code.
"""

from typing import Any, Dict, Optional

from opendxa.dana.poet import POETConfig, POETExecutor
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def poet_function(
    context: SandboxContext,
    func_name: str,
    args: Optional[list] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    domain: Optional[str] = None,
    timeout: Optional[float] = None,
    retries: Optional[int] = None,
    enable_training: bool = True,
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
    config = POETConfig(
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
    original_func, func_type, metadata = registry.resolve(func_name)

    # Create POET executor and wrap the function
    poe_executor = POETExecutor(config)

    # Create a wrapper function that will be enhanced by POE
    def target_function(*call_args, **call_kwargs):
        return registry.call(func_name, context, None, *call_args, **call_kwargs)

    # Apply POET enhancement to the wrapper
    enhanced_function = poe_executor(target_function)

    # Call the enhanced function with the provided arguments
    return enhanced_function(*args, **kwargs)


def apply_poet_function(
    context: SandboxContext,
    operation: Any,
    config: Optional[Dict[str, Any]] = None,
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
    poe_config = POETConfig(
        domain=config.get("domain"),
        timeout=config.get("timeout", 30.0),
        retries=config.get("retries", 2),
        enable_training=config.get("enable_training", True),
    )

    # Create POET executor and apply enhancement
    poe_executor = POETExecutor(poe_config)
    enhanced_operation = poe_executor(operation)

    # Call the enhanced operation
    return enhanced_operation()
