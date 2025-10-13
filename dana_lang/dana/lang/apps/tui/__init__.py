"""
Dana TUI - Multi-Agent REPL Terminal User Interface.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Only expose the main public interface
from .tui_app import DanaTUI
from .tui_app import main as tui_main

__all__ = ["tui_main", "DanaTUI"]
