"""
General Problem Solver with Expert Workflows

This package provides a unified interface for agents to solve problems by intelligently routing
them to specialized workflows contained in existing Dana modules.
"""

from .solver import solve, GeneralProblemSolver, WorkflowInfo, ResourceMatch

__all__ = [
    "solve",
    "GeneralProblemSolver",
    "WorkflowInfo",
    "ResourceMatch"
]
