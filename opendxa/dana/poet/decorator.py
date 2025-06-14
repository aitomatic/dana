"""POET Decorator - @poet() implementation for function enhancement"""

import inspect
import functools
from typing import Any, Callable, Optional

from opendxa.common.utils.logging import DXA_LOGGER
from .client import get_default_client
from .types import POETConfig, POETResult, POETServiceError


def poet(
    domain: Optional[str] = None,
    optimize_for: Optional[str] = None,
    retries: int = 3,
    timeout: float = 30.0,
    enable_monitoring: bool = True,
) -> Callable:
    """
    POET decorator for automatic function enhancement with P→O→E→(T) phases

    Args:
        domain: Domain template to use (e.g., "ml_monitoring", "api_operations")
        optimize_for: Optimization objective (enables Train phase when specified)
        retries: Number of retry attempts for operations
        timeout: Timeout in seconds for operations
        enable_monitoring: Whether to enable execution monitoring

    Returns:
        Enhanced function with POET capabilities

    Example:
        @poet(domain="ml_monitoring", optimize_for="accuracy")
        def detect_drift(current_data, reference_data):
            return {"drift_detected": False, "score": 0.0}
    """

    def decorator(func: Callable) -> Callable:
        # Create POET configuration
        config = POETConfig(domain=domain, optimize_for=optimize_for, retries=retries, timeout=timeout, enable_monitoring=enable_monitoring)

        # Get function source code
        try:
            source_code = inspect.getsource(func)
        except Exception as e:
            DXA_LOGGER.warning(f"Could not get source for {func.__name__}: {e}")
            source_code = f"def {func.__name__}(): pass  # Source unavailable"

        # Create enhanced function
        @functools.wraps(func)
        def enhanced_wrapper(*args, **kwargs):
            return _execute_enhanced_function(func, config, source_code, *args, **kwargs)

        # Store POET metadata
        enhanced_wrapper._poet_config = config
        enhanced_wrapper._poet_original = func
        enhanced_wrapper._poet_source = source_code

        return enhanced_wrapper

    return decorator


def _execute_enhanced_function(original_func: Callable, config: POETConfig, source_code: str, *args, **kwargs) -> POETResult:
    """Execute the enhanced version of a POET function"""

    function_name = original_func.__name__

    try:
        # Get POET client
        client = get_default_client()

        # Prepare execution context
        context = {"function_name": function_name, "args": args, "kwargs": kwargs, "module": getattr(original_func, "__module__", None)}

        # Check if we have a cached enhanced version
        enhanced_func = _get_or_create_enhanced_function(client, original_func, config, source_code, context)

        # Execute enhanced function
        DXA_LOGGER.debug(f"Executing enhanced {function_name}")
        result = enhanced_func(*args, **kwargs)

        # Ensure result is wrapped as POETResult
        if not isinstance(result, POETResult):
            result = POETResult(result, function_name, "v1")

        return result

    except Exception as e:
        DXA_LOGGER.error(f"POET execution failed for {function_name}: {e}")

        # Fallback to original function on enhancement failure
        DXA_LOGGER.info(f"Falling back to original {function_name}")
        original_result = original_func(*args, **kwargs)
        return POETResult(original_result, function_name, "original")


def _get_or_create_enhanced_function(client, original_func: Callable, config: POETConfig, source_code: str, context: dict) -> Callable:
    """Get cached enhanced function or create new one via transpilation"""

    function_name = original_func.__name__

    # Check if enhanced version exists in cache/storage
    # For Alpha: simple in-memory cache
    cache_key = f"{function_name}_{hash(source_code)}_{hash(str(config.dict()))}"

    if hasattr(_get_or_create_enhanced_function, "_cache"):
        cached_func = _get_or_create_enhanced_function._cache.get(cache_key)
        if cached_func:
            DXA_LOGGER.debug(f"Using cached enhanced {function_name}")
            return cached_func
    else:
        _get_or_create_enhanced_function._cache = {}

    # Transpile function to get enhanced version
    DXA_LOGGER.info(f"Transpiling {function_name} with POET")

    try:
        transpiled = client.transpile_function(source_code, config, context)

        # Execute the generated code to get the function
        namespace = {}
        exec(transpiled.code, namespace)

        # Find the enhanced function (should be named {original_name}_enhanced)
        enhanced_name = f"{function_name}_enhanced"
        if enhanced_name not in namespace:
            # Look for any function that might be the enhanced version
            functions = [v for v in namespace.values() if callable(v) and hasattr(v, "__name__")]
            if functions:
                enhanced_func = functions[0]  # Use first function found
            else:
                raise POETServiceError("No enhanced function found in transpiled code")
        else:
            enhanced_func = namespace[enhanced_name]

        # Cache the enhanced function
        _get_or_create_enhanced_function._cache[cache_key] = enhanced_func

        DXA_LOGGER.info(f"Successfully created enhanced {function_name}")
        return enhanced_func

    except Exception as e:
        DXA_LOGGER.error(f"Failed to create enhanced {function_name}: {e}")
        raise POETServiceError(f"Enhancement failed: {e}")


# Feedback API function
def feedback(result: POETResult, feedback_payload: Any) -> None:
    """
    Submit feedback for a POET function execution

    Args:
        result: POETResult from function execution
        feedback_payload: Any feedback data (will be processed by LLM)

    Example:
        result = my_poet_function(data)
        poet.feedback(result, "The drift detection was too sensitive")
    """
    client = get_default_client()
    client.feedback(result, feedback_payload)
