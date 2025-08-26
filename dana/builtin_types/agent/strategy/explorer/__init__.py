"""
Parallel Exploration Strategy Module

This module implements the strategy where multiple solution candidates
are tried simultaneously with early termination of underperforming ones.
"""

from .explorer_strategy import ExplorerStrategy

__all__ = ["ExplorerStrategy"]
