"""Solver mixins for agent problem-solving capabilities."""

from .base import BaseSolver, SignatureMatcher, SolverResponse
from dana.registry import WorkflowRegistry, ResourceRegistry
from .planner_executor import PlannerExecutorSolver
from .reactive_support import ReactiveSupportSolver
from .simple_helpful import SimpleHelpfulSolver
from .triage import TriageSolver

__all__ = [
    "BaseSolver",
    "WorkflowRegistry",
    "ResourceRegistry",
    "SignatureMatcher",
    "SolverResponse",
    "PlannerExecutorSolver",
    "ReactiveSupportSolver",
    "SimpleHelpfulSolver",
    "TriageSolver",
]
