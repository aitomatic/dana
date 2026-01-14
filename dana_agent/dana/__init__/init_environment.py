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

        def get_logger(name: str | None = None) -> logging.Logger:
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name or "dana")

        def configure(*_args: object, **_kwargs: object) -> None:
            return None

        def make_filtering_bound_logger(_level: int) -> type[logging.Logger]:
            return logging.Logger

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


def init_environment():
    """Load environment variables from .env file."""
    _install_structlog_shim()
    _install_langfuse_shim()
    dotenv_path = find_dotenv()
    print(f"Loading environment variables from {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
