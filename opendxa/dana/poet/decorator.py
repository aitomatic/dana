"""POET Decorator - @poet() implementation for function enhancement"""

import atexit
import functools
import inspect
from collections.abc import Callable
from typing import Any

from opendxa.api.client import APIClient
from opendxa.api.service_manager import APIServiceManager
from opendxa.common.mixins.loggable import Loggable

from .types import POETConfig, POETResult, POETServiceError, TranspiledFunction


class POETDecorator(Loggable):
    """POET decorator implementation with logging support"""

    def __init__(self):
        super().__init__()
        self._global_poet_service: APIServiceManager | None = None
        self._global_poet_client: APIClient | None = None
        self._cleanup_registered = False

    def _cleanup_global_poet_service(self):
        """Cleanup global POET service at process exit"""
        try:
            if self._global_poet_client:
                self._global_poet_client.shutdown()
                self._global_poet_client = None

            if self._global_poet_service:
                self._global_poet_service.shutdown()
                self._global_poet_service = None

            self.log_info("Global POET API service cleaned up")
        except Exception as e:
            self.log_error(f"Error cleaning up global POET service: {e}")

    def get_poet_api_client(self) -> APIClient:
        """Get or create global POET API client for standalone usage"""
        if self._global_poet_client is None:
            self.log_info("Initializing global POET API service")

            # Create and start API service
            self._global_poet_service = APIServiceManager()
            self._global_poet_service.startup()

            # Get and start client
            self._global_poet_client = self._global_poet_service.get_client()
            self._global_poet_client.startup()

            # Register cleanup on first use
            if not self._cleanup_registered:
                atexit.register(self._cleanup_global_poet_service)
                self._cleanup_registered = True

            self.log_info("Global POET API service ready")

        return self._global_poet_client

    def _execute_enhanced_function(self, original_func: Callable, config: POETConfig, source_code: str, *args, **kwargs) -> POETResult:
        """Execute the enhanced version of a POET function"""
        function_name = original_func.__name__

        try:
            # Get POET API client
            api_client = self.get_poet_api_client()

            # Prepare execution context
            context = {
                "function_name": function_name,
                "args": args,
                "kwargs": kwargs,
                "module": getattr(original_func, "__module__", None),
            }

            # Check if we have a cached enhanced version
            enhanced_func = self._get_or_create_enhanced_function(api_client, original_func, config, source_code, context)

            # Execute enhanced function
            self.log_debug(f"Executing enhanced {function_name}")
            result = enhanced_func(*args, **kwargs)

            # Ensure result is wrapped as POETResult
            if not isinstance(result, POETResult):
                result = POETResult(result, function_name, "v1")

            return result

        except Exception as e:
            self.log_error(f"POET execution failed for {function_name}: {e}")

            # Fallback to original function on enhancement failure
            self.log_info(f"Falling back to original {function_name}")
            original_result = original_func(*args, **kwargs)
            return POETResult(original_result, function_name, "original")

    def _get_or_create_enhanced_function(
        self, client, original_func: Callable, config: POETConfig, source_code: str, context: dict
    ) -> Callable:
        """Get cached enhanced function or create new one via transpilation"""
        function_name = original_func.__name__

        # Check if enhanced version exists in cache/storage
        # For Alpha: simple in-memory cache
        cache_key = f"{function_name}_{hash(source_code)}_{hash(str(config.dict()))}"

        if hasattr(self._get_or_create_enhanced_function, "_cache"):
            cached_func = self._get_or_create_enhanced_function._cache.get(cache_key)
            if cached_func:
                self.log_debug(f"Using cached enhanced {function_name}")
                return cached_func
        else:
            self._get_or_create_enhanced_function._cache = {}

        # Transpile function to get enhanced version
        self.log_info(f"Transpiling {function_name} with POET")

        try:
            # Call API to transpile function
            request_data = {
                "function_code": source_code,
                "language": "python",
                "config": config.dict(),
            }

            if context:
                request_data["context"] = context

            # Use /poet prefix for POET-specific endpoints
            response_data = client.post("/poet/transpile", request_data)
            transpiled = TranspiledFunction.from_response(response_data)

            # Execute the generated code to get the function
            namespace = {
                f"_original_{function_name}": original_func,  # Inject original function
            }
            exec(transpiled.code, namespace)

            # Find the enhanced function (should be named {original_name}_enhanced)
            enhanced_name = f"{function_name}_enhanced"
            if enhanced_name not in namespace:
                # Look for any function that might be the enhanced version
                functions = [v for v in namespace.values() if callable(v) and hasattr(v, "__name__")]
                if functions:
                    enhanced_func = functions[0]  # Use first function found
                else:
                    raise POETServiceError(f"No enhanced function found in transpiled code for {function_name}")
            else:
                enhanced_func = namespace[enhanced_name]

            # Cache the enhanced function
            self._get_or_create_enhanced_function._cache[cache_key] = enhanced_func

            return enhanced_func

        except Exception as e:
            self.log_error(f"Failed to transpile {function_name}: {e}")
            raise POETServiceError(f"Transpilation failed: {str(e)}")


# Global POET decorator instance
_poet_decorator = POETDecorator()


def poet(
    domain: str | None = None,
    optimize_for: str | None = None,
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
        config = POETConfig(
            domain=domain,
            optimize_for=optimize_for,
            retries=retries,
            timeout=timeout,
            enable_monitoring=enable_monitoring,
        )

        # Get function source code
        try:
            source_code = inspect.getsource(func)
            # Fix indentation issues - dedent to remove leading whitespace
            import textwrap

            source_code = textwrap.dedent(source_code)
        except Exception as e:
            _poet_decorator.log_warning(f"Could not get source for {func.__name__}: {e}")
            source_code = f"def {func.__name__}(): pass  # Source unavailable"

        # Create enhanced function
        @functools.wraps(func)
        def enhanced_wrapper(*args, **kwargs):
            return _poet_decorator._execute_enhanced_function(func, config, source_code, *args, **kwargs)

        # Store POET metadata
        enhanced_wrapper._poet_config = config
        enhanced_wrapper._poet_original = func
        enhanced_wrapper._poet_source = source_code

        return enhanced_wrapper

    return decorator


def feedback(result: POETResult, feedback_payload: Any) -> None:
    """Submit feedback for a POET function execution"""
    try:
        # Get POET API client
        api_client = _poet_decorator.get_poet_api_client()

        # Submit feedback
        request_data = {
            "execution_id": result.execution_id,
            "function_name": result.function_name,
            "feedback_payload": feedback_payload,
        }

        api_client.post("/poet/feedback", request_data)
        _poet_decorator.log_info(f"Feedback submitted for {result.function_name} execution {result.execution_id}")

    except Exception as e:
        _poet_decorator.log_error(f"Failed to submit feedback: {e}")
        raise POETServiceError(f"Feedback submission failed: {str(e)}")
