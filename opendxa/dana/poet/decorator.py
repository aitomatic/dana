"""POET Decorator - @poet() implementation for function enhancement"""

import functools
import inspect
from collections.abc import Callable
from typing import Any

from opendxa.common.utils.logging import DXA_LOGGER

from .types import POETConfig


class POETDecorator:
    """POET decorator implementation"""

    _instances: dict[Callable[..., Any], "POETDecorator"] = {}

    def __init__(self, poet_config: "POETConfig"):
        self.poet_config = poet_config
        self.client = None  # Lazy initialization
        self._cache: dict[str, Any] = {}

    def _get_client(self):
        if not self.client:
            from .client import get_default_client

            self.client = get_default_client()
        return self.client


    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        POETDecorator._instances[func] = self

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            DXA_LOGGER.info(f"Executing POET-enhanced function: {func.__name__}")

            try:
                source_code = inspect.getsource(func)
            except TypeError as e:
                DXA_LOGGER.error(f"Could not get source code for {func.__name__}: {e}")
                return func(*args, **kwargs)

            if source_code in self._cache:
                DXA_LOGGER.info(f"Using cached enhanced function for {func.__name__}")
                enhanced_func = self._cache[source_code]
                return enhanced_func(*args, **kwargs)

            try:
                client = self._get_client()
                enhanced_func_code = client.transpile(source_code, self.poet_config)
                DXA_LOGGER.info(f"Transpiled code for {func.__name__}: {enhanced_func_code}")

                # This is a placeholder for actual execution
                result = func(*args, **kwargs)

                self._cache[source_code] = func  # Caching original function for now
                return result

            except Exception as e:
                DXA_LOGGER.error(f"POET enhancement failed for {func.__name__}: {e}. Falling back to original function.")
                return func(*args, **kwargs)

        return wrapper


def poet(
    domain: str | None = None,
    optimize_for: str | None = None,
    retries: int = 3,
    timeout: int = 30,
    enable_monitoring: bool = True,
    enable_training: bool = False,
) -> POETDecorator:
    """
    Decorator to enhance a Python function using POET.
    """
    poet_config = POETConfig(
        domain=domain,
        optimize_for=optimize_for,
        retries=retries,
        timeout=timeout,
        enable_monitoring=enable_monitoring,
        enable_training=enable_training,
    )
    return POETDecorator(poet_config)
