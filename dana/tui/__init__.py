"""
Dana TUI - Multi-Agent REPL Terminal User Interface.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Only expose the main public interface
from .app import DanaTUI

__all__ = ["DanaTUI"]
