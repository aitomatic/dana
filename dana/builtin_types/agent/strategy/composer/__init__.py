"""
Capability Composition Strategy Module

This module implements the strategy where the agent analyzes problem requirements
and composes multiple strategies into an execution chain.
"""

from .composer_strategy import ComposerStrategy

__all__ = ["ComposerStrategy"]
