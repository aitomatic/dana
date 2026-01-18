"""
Local import shim for `dana` when running from the repo root.

This makes `import dana` resolve to `dana_agent/dana` without requiring
manual PYTHONPATH tweaks.
"""

from __future__ import annotations

from importlib import import_module
import sys
import types
import logging
from pathlib import Path


_pkg_root = Path(__file__).resolve().parent
_agent_pkg = _pkg_root.parent / "dana_agent" / "dana"
_pkg_paths = globals().setdefault("__path__", [])

if _agent_pkg.exists():
    _pkg_paths.append(str(_agent_pkg))


def _install_structlog_shim() -> None:
    try:
        import structlog  # noqa: F401
    except ModuleNotFoundError:
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


_install_structlog_shim()
_install_langfuse_shim()

_common = import_module("dana.common")
_core = import_module("dana.core")

LLM = _common.LLM
LLMMessage = _common.LLMMessage
LLMResponse = _common.LLMResponse
STARAgent = _core.STARAgent

__all__ = ["LLM", "LLMMessage", "LLMResponse", "STARAgent"]
