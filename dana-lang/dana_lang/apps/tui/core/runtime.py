"""
Runtime system for Dana agents in the TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana_lang.core.lang.dana_sandbox import DanaSandbox, ExecutionResult

# Re-export the core DanaSandbox for TUI usage
__all__ = ["DanaSandbox", "ExecutionResult"]
