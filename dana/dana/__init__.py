"""
Dana Language - Backward Compatibility Shim

This package provides backward compatibility for code using 'import dana'.
All functionality is re-exported from dana_lang.

DEPRECATED: Please use 'import dana_lang' directly in new code.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "\n"
    "=" * 70 + "\n"
    "DEPRECATION WARNING: 'import dana' is deprecated.\n"
    "Please use 'from dana_lang import ...' instead.\n"
    "\n"
    "This compatibility shim will be removed in a future version.\n"
    "=" * 70,
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from dana_lang
from dana_lang import *  # noqa: F403, F401

# Explicitly re-export common items to help IDEs
from dana_lang import (  # noqa: F401
    DANA_LOGGER,
    DanaParser,
    DanaSandbox,
    __version__,
    py2na,
)

__all__ = [
    "__version__",
    "DANA_LOGGER",
    "DanaParser",
    "DanaSandbox",
    "py2na",
]
