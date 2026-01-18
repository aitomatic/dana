"""
Dana Agent - Domain-Aware Neurosymbolic Agents

This package provides the core agent framework for building and managing
specialized AI agents with domain-specific knowledge and capabilities.
"""

import sys
import types

from dotenv import find_dotenv, load_dotenv


def _install_structlog_shim() -> None:
    try:
        import structlog  # noqa: F401
    except ModuleNotFoundError:
        import logging

        shim = types.ModuleType("structlog")

        class _BoundLogger:
            def __init__(self, logger: logging.Logger) -> None:
                self._logger = logger

            def bind(self, **_kwargs: object) -> "_BoundLogger":
                return self

            def _format(self, message: str, **kwargs: object) -> str:
                if not kwargs:
                    return message
                return f"{message} {kwargs}"

            def debug(self, message: str, **kwargs: object) -> None:
                self._logger.debug(self._format(message, **kwargs))

            def info(self, message: str, **kwargs: object) -> None:
                self._logger.info(self._format(message, **kwargs))

            def warning(self, message: str, **kwargs: object) -> None:
                self._logger.warning(self._format(message, **kwargs))

            def error(self, message: str, **kwargs: object) -> None:
                self._logger.error(self._format(message, **kwargs))

        def get_logger(name: str | None = None) -> _BoundLogger:
            logging.basicConfig(level=logging.INFO)
            return _BoundLogger(logging.getLogger(name or "dana"))

        def configure(*_args: object, **_kwargs: object) -> None:
            return None

        def make_filtering_bound_logger(_level: int) -> type[_BoundLogger]:
            return _BoundLogger

        shim.get_logger = get_logger
        shim.configure = configure
        shim.make_filtering_bound_logger = make_filtering_bound_logger

        sys.modules["structlog"] = shim


def _install_langfuse_shim() -> None:
    try:
        import langfuse  # noqa: F401
    except ModuleNotFoundError:
        shim = types.ModuleType("langfuse")

        class Langfuse:
            def flush(self) -> None:
                return None

        def observe(*args: object, **kwargs: object):
            def decorator(func):
                return func

            if len(args) == 1 and callable(args[0]) and not kwargs:
                return args[0]
            return decorator

        shim.Langfuse = Langfuse
        shim.observe = observe

        sys.modules["langfuse"] = shim


def init_environment(verbose: bool = False):
    """Load environment variables from .env file.

    Args:
        verbose: If True, print status messages. Default is False (quiet).
    """
    _install_structlog_shim()
    _install_langfuse_shim()
    dotenv_path = find_dotenv()
    if verbose:
        print(f"Loading environment variables from {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
