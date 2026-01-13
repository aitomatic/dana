"""
Retry handler with exponential backoff for production robustness.

Provides decorators and utilities for retrying failed operations with
configurable backoff strategies.
"""

import time
import functools
from typing import Callable, Any


def with_retry(max_attempts: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between attempts (default: 2.0)
        exceptions: Tuple of exception types to catch (default: all Exception)

    Example:
        @with_retry(max_attempts=5, initial_delay=2.0)
        def fetch_data(url):
            # May fail due to network issues
            return requests.get(url)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        # Last attempt failed, re-raise
                        print(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    # Calculate delay with exponential backoff
                    wait_time = delay * (backoff_factor ** (attempt - 1))

                    print(f"⚠️  {func.__name__} attempt {attempt}/{max_attempts} failed: {e}")
                    print(f"   Retrying in {wait_time:.1f}s...")

                    time.sleep(wait_time)

            # Should never reach here
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to a function.

    Args:
        timeout_seconds: Maximum time to allow function to run

    Example:
        @with_timeout(30.0)
        def slow_operation():
            # Will be interrupted if it takes > 30 seconds
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} exceeded timeout of {timeout_seconds}s")

            # Set the signal handler
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout_seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # Cancel the alarm
                signal.alarm(0)

            return result

        return wrapper

    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations with fallback.

    Example:
        with RetryableOperation(fallback_value=[]) as op:
            result = op.execute(fetch_data, url="https://example.com")
    """

    def __init__(self, fallback_value: Any = None, max_attempts: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        """
        Initialize retryable operation.

        Args:
            fallback_value: Value to return if all attempts fail
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay between retries
            backoff_factor: Exponential backoff multiplier
        """
        self.fallback_value = fallback_value
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.last_exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Suppress exceptions if fallback is provided
        if exc_type is not None and self.fallback_value is not None:
            return True
        return False

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result or fallback_value on failure
        """
        delay = self.initial_delay

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                self.last_exception = e

                if attempt == self.max_attempts:
                    print(f"❌ Operation failed after {self.max_attempts} attempts: {e}")
                    if self.fallback_value is not None:
                        print("   Using fallback value")
                        return self.fallback_value
                    raise

                wait_time = delay * (self.backoff_factor ** (attempt - 1))
                print(f"⚠️  Attempt {attempt}/{self.max_attempts} failed: {e}")
                print(f"   Retrying in {wait_time:.1f}s...")

                time.sleep(wait_time)

        return self.fallback_value
