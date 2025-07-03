"""Dana Logging"""

# Import from dana structure
from .dana_logger import DXA_LOGGER, DANA_LOGGER, DXALogger

# Also maintain compatibility with old path
from .dxa_logger import DXA_LOGGER as DXA_LOGGER_COMPAT

__all__ = ["DXALogger", "DXA_LOGGER", "DANA_LOGGER"]
