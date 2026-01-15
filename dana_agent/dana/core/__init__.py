"""
Core module for the Adana agentic architecture.

This module provides the core components for building conversational AI agents
with resource and workflow management.
"""

__all__ = ["STARAgent"]


def __getattr__(name: str):
    if name == "STARAgent":
        from .agent import STARAgent

        return STARAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
