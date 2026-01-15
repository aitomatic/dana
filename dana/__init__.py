"""Namespace shim for local development.

Allows `import dana` to resolve to `dana_agent/dana` without installing the package.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path
import logging
import sys
import types


def _install_structlog_stub() -> None:
    if "structlog" in sys.modules:
        return
    try:
        import structlog  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class _StructLogAdapter:
        def __init__(self, logger: logging.Logger) -> None:
            self._logger = logger

        def _format(self, message: str, kwargs: dict) -> str:
            if not kwargs:
                return message
            details = " ".join(f"{key}={value}" for key, value in kwargs.items())
            return f"{message} {details}"

        def _log(self, level: str, message: str, **kwargs) -> None:
            getattr(self._logger, level)(self._format(message, kwargs))

        def info(self, message: str, **kwargs) -> None:
            self._log("info", message, **kwargs)

        def warning(self, message: str, **kwargs) -> None:
            self._log("warning", message, **kwargs)

        def error(self, message: str, **kwargs) -> None:
            self._log("error", message, **kwargs)

        def debug(self, message: str, **kwargs) -> None:
            self._log("debug", message, **kwargs)

        def bind(self, **kwargs):  # noqa: ANN001
            return self

    def get_logger(name: str | None = None):  # noqa: ANN001
        logging.basicConfig(level=logging.INFO)
        return _StructLogAdapter(logging.getLogger(name or "dana"))

    stub = types.SimpleNamespace(get_logger=get_logger)
    sys.modules["structlog"] = stub


_install_structlog_stub()


package_root = Path(__file__).resolve().parent
dana_agent_root = package_root.parent / "dana_agent"
if dana_agent_root.is_dir() and str(dana_agent_root) not in sys.path:
    sys.path.insert(0, str(dana_agent_root))

__path__ = extend_path(__path__, __name__)
