"""
Dana Language Server Protocol (LSP) implementation.

This package provides LSP support for the Dana language, enabling
rich editor features like diagnostics, hover information, go-to-definition,
and auto-completion.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

try:
    from lsprotocol import types as lsp
    from pygls.server import LanguageServer
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

if LSP_AVAILABLE:
    from .server import main as start_server
    __all__ = ['start_server']
else:
    __all__ = [] 