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
    ObjectiveType,
    ObjectivePriority,
    ObjectiveFunction,
    MultiObjective,
    ObjectiveEvaluationResult,
)

from .registry import POETObjectiveRegistry, get_global_registry

from .evaluator import ObjectiveEvaluator, EvaluationContext

from .domain_objectives import (
    BuildingManagementObjectives,
    LLMOptimizationObjectives,
    FinancialServicesObjectives,
    CommonObjectives,
    get_domain_objectives,
)

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
