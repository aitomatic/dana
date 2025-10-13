"""
Dana Language Server Protocol (LSP) implementation.

This package provides LSP support for the Dana language, enabling
rich editor features like diagnostics, hover information, go-to-definition,
and auto-completion.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import importlib.util

# Check if LSP dependencies are available
LSP_AVAILABLE = importlib.util.find_spec("lsprotocol") is not None and importlib.util.find_spec("pygls") is not None

if LSP_AVAILABLE:
    from .server import main as start_server

    __all__ = ["start_server"]
else:
    __all__ = []
