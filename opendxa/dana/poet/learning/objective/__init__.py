"""
POET Learning Objective Framework

This module implements formal objective functions for POET learning systems,
based on learning theory principles that every learning system must optimize
well-defined objectives subject to constraints.

Key Components:
- ObjectiveFunction: Individual objective definitions
- MultiObjective: Multi-objective optimization with trade-offs
- POETObjectiveRegistry: Domain-specific objective registrations
- ObjectiveEvaluator: Runtime objective evaluation engine
"""

from .base import (
    MultiObjective,
    ObjectiveEvaluationResult,
    ObjectiveFunction,
    ObjectivePriority,
    ObjectiveType,
)
from .domain_objectives import (
    BuildingManagementObjectives,
    CommonObjectives,
    FinancialServicesObjectives,
    LLMOptimizationObjectives,
    get_domain_objectives,
)
from .evaluator import EvaluationContext, ObjectiveEvaluator
from .registry import POETObjectiveRegistry, get_global_registry

__all__ = [
    # Core objective framework
    "ObjectiveType",
    "ObjectivePriority",
    "ObjectiveFunction",
    "MultiObjective",
    "ObjectiveEvaluationResult",
    # Registry and evaluation
    "POETObjectiveRegistry",
    "ObjectiveEvaluator",
    "EvaluationContext",
    "get_global_registry",
    # Domain-specific objectives
    "BuildingManagementObjectives",
    "LLMOptimizationObjectives",
    "FinancialServicesObjectives",
    "CommonObjectives",
    "get_domain_objectives",
]
