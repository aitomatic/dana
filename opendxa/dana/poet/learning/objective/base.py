"""
Core Objective Framework Base Classes

Implements formal learning theory foundations:
- Every learning system optimizes: f(θ) subject to constraints C
- Multi-objective: optimize (f1, f2, ..., fn) with trade-offs
- Constrained optimization: optimize f(θ) subject to g(θ) ≤ 0, h(θ) = 0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import time
from opendxa.common.utils.logging import DXA_LOGGER


class ObjectiveType(Enum):
    """Types of objectives in POET learning systems."""

    MINIMIZE = "minimize"  # Minimize cost, time, errors
    MAXIMIZE = "maximize"  # Maximize efficiency, quality, success rate
    TARGET = "target"  # Reach specific target value with tolerance
    CONSTRAINT = "constraint"  # Hard constraint (feasibility requirement)


class ObjectivePriority(Enum):
    """Priority levels for objectives in constraint hierarchies."""

    CRITICAL = 1  # Safety, compliance - never violate
    HIGH = 2  # Performance requirements - rarely violate
    MEDIUM = 3  # Optimization goals - can violate temporarily
    LOW = 4  # Nice-to-have improvements


@dataclass
class ObjectiveFunction:
    """
    Formal definition of a single learning objective.

    Examples:
    - minimize(execution_time) subject to success_rate >= 0.95
    - maximize(energy_efficiency) with weight 0.6
    - target(response_time = 100ms) with tolerance ±10ms
    - constraint(safety_score >= 0.95) with CRITICAL priority
    """

    name: str
    type: ObjectiveType
    priority: ObjectivePriority

    # Objective definition
    metric_name: str  # What metric to optimize
    weight: float = 1.0  # Relative importance (0.0-1.0)

    # Target objectives
    target_value: Optional[float] = None  # For TARGET objectives
    tolerance: Optional[float] = None  # Acceptable deviation from target

    # Constraint bounds
    min_value: Optional[float] = None  # Lower bound constraint
    max_value: Optional[float] = None  # Upper bound constraint

    # Advanced objective functions
    objective_func: Optional[Callable[[Dict[str, float]], float]] = None
    constraint_func: Optional[Callable[[Dict[str, float]], bool]] = None

    # Metadata
    description: str = ""
    unit: str = ""

    def __post_init__(self):
        """Validate objective function definition."""
        if self.type == ObjectiveType.TARGET and self.target_value is None:
            raise ValueError(f"TARGET objective '{self.name}' must specify target_value")

        if self.type == ObjectiveType.CONSTRAINT and (self.min_value is None and self.max_value is None and self.constraint_func is None):
            raise ValueError(f"CONSTRAINT objective '{self.name}' must specify bounds or constraint_func")

        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")

    def evaluate(self, metrics: Dict[str, float]) -> float:
        """
        Evaluate objective function given current metrics.

        Returns:
            float: Objective value (higher is better for optimization)
                  -inf for constraint violations
        """
        # Use custom function if provided
        if self.objective_func:
            try:
                return self.objective_func(metrics)
            except Exception as e:
                DXA_LOGGER.warning(f"Custom objective function failed for {self.name}: {e}")
                return -float("inf")

        # Get metric value
        value = metrics.get(self.metric_name, 0.0)

        if self.type == ObjectiveType.MINIMIZE:
            # Return negative value for minimization (higher = better)
            return -value

        elif self.type == ObjectiveType.MAXIMIZE:
            # Return positive value for maximization
            return value

        elif self.type == ObjectiveType.TARGET:
            # Target objective: score based on distance from target
            if self.target_value is not None:
                error = abs(value - self.target_value)
                tolerance = self.tolerance or (self.target_value * 0.1)  # Default 10% tolerance
                if tolerance > 0:
                    # Score from 0 to 1 based on closeness to target
                    score = max(0.0, 1.0 - error / tolerance)
                    return score
                else:
                    # Exact match required
                    return 1.0 if error == 0 else 0.0
            return 0.0

        elif self.type == ObjectiveType.CONSTRAINT:
            # Constraint: return 0 if satisfied, -inf if violated
            return self._evaluate_constraint(value)

        return 0.0

    def _evaluate_constraint(self, value: float) -> float:
        """Evaluate constraint satisfaction."""
        # Use custom constraint function if provided
        if self.constraint_func:
            try:
                return 0.0 if self.constraint_func({self.metric_name: value}) else -float("inf")
            except Exception as e:
                DXA_LOGGER.warning(f"Custom constraint function failed for {self.name}: {e}")
                return -float("inf")

        # Check bounds
        if self.min_value is not None and value < self.min_value:
            return -float("inf")  # Constraint violation

        if self.max_value is not None and value > self.max_value:
            return -float("inf")  # Constraint violation

        return 0.0  # Constraint satisfied

    def is_constraint_satisfied(self, metrics: Dict[str, float]) -> bool:
        """Check if constraint is satisfied without evaluating objective."""
        if self.type != ObjectiveType.CONSTRAINT:
            return True

        value = metrics.get(self.metric_name, 0.0)
        return self._evaluate_constraint(value) != -float("inf")

    def get_violation_message(self, metrics: Dict[str, float]) -> Optional[str]:
        """Get human-readable constraint violation message."""
        if self.type != ObjectiveType.CONSTRAINT:
            return None

        if self.is_constraint_satisfied(metrics):
            return None

        value = metrics.get(self.metric_name, 0.0)

        if self.min_value is not None and value < self.min_value:
            return f"{self.name}: {value:.3f} < {self.min_value} (minimum required)"

        if self.max_value is not None and value > self.max_value:
            return f"{self.name}: {value:.3f} > {self.max_value} (maximum allowed)"

        return f"{self.name}: constraint violation"


@dataclass
class ObjectiveEvaluationResult:
    """Result of multi-objective evaluation."""

    feasible: bool  # All constraints satisfied
    total_score: float  # Overall optimization score
    individual_scores: Dict[str, float]  # Score for each objective
    constraint_violations: List[str] = field(default_factory=list)  # Violated constraints
    optimization_method: str = "weighted_sum"  # Method used
    evaluation_time: float = 0.0  # Time taken to evaluate
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info


@dataclass
class MultiObjective:
    """
    Multi-objective optimization with trade-offs.

    Implements multiple optimization approaches:
    - weighted_sum: Simple weighted combination
    - lexicographic: Priority-ordered optimization
    - constraint_satisfaction: Feasibility first, then optimization
    - pareto: Pareto-efficient solutions (future)
    """

    name: str
    objectives: List[ObjectiveFunction]
    method: str = "constraint_satisfaction"  # Default to constraint satisfaction

    # Method-specific parameters
    normalize_scores: bool = True  # Normalize scores to [0,1] range
    constraint_penalty: float = 1000.0  # Penalty for constraint violations

    def __post_init__(self):
        """Validate multi-objective configuration."""
        valid_methods = ["weighted_sum", "lexicographic", "constraint_satisfaction", "pareto"]
        if self.method not in valid_methods:
            raise ValueError(f"Invalid method '{self.method}'. Must be one of: {valid_methods}")

        if not self.objectives:
            raise ValueError("Must specify at least one objective")

        # Validate weight normalization for weighted sum
        if self.method == "weighted_sum":
            total_weight = sum(obj.weight for obj in self.objectives if obj.type != ObjectiveType.CONSTRAINT)
            if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                DXA_LOGGER.warning(f"Objective weights sum to {total_weight:.3f}, not 1.0. Consider normalizing.")

    def evaluate(self, metrics: Dict[str, float]) -> ObjectiveEvaluationResult:
        """Evaluate multi-objective function."""
        start_time = time.time()

        try:
            if self.method == "weighted_sum":
                result = self._weighted_sum(metrics)
            elif self.method == "lexicographic":
                result = self._lexicographic(metrics)
            elif self.method == "constraint_satisfaction":
                result = self._constraint_satisfaction(metrics)
            elif self.method == "pareto":
                result = self._pareto_optimization(metrics)
            else:
                raise ValueError(f"Unknown optimization method: {self.method}")

            result.evaluation_time = time.time() - start_time
            return result

        except Exception as e:
            DXA_LOGGER.error(f"Multi-objective evaluation failed: {e}")
            return ObjectiveEvaluationResult(
                feasible=False,
                total_score=-float("inf"),
                individual_scores={},
                constraint_violations=[f"Evaluation error: {str(e)}"],
                optimization_method=self.method,
                evaluation_time=time.time() - start_time,
            )

    def _weighted_sum(self, metrics: Dict[str, float]) -> ObjectiveEvaluationResult:
        """Weighted sum approach - simple but can miss trade-offs."""
        total_score = 0.0
        individual_scores = {}
        constraint_violations = []

        # Separate constraints from objectives
        constraints = [obj for obj in self.objectives if obj.type == ObjectiveType.CONSTRAINT]
        optimization_objectives = [obj for obj in self.objectives if obj.type != ObjectiveType.CONSTRAINT]

        # Check constraints first
        for constraint in constraints:
            score = constraint.evaluate(metrics)
            if score == -float("inf"):
                violation_msg = constraint.get_violation_message(metrics)
                if violation_msg:
                    constraint_violations.append(violation_msg)

        # If critical constraints violated, return infeasible
        critical_violations = [
            obj for obj in constraints if obj.priority == ObjectivePriority.CRITICAL and not obj.is_constraint_satisfied(metrics)
        ]

        if critical_violations:
            return ObjectiveEvaluationResult(
                feasible=False,
                total_score=-float("inf"),
                individual_scores={obj.name: obj.evaluate(metrics) for obj in self.objectives},
                constraint_violations=constraint_violations,
                optimization_method="weighted_sum",
            )

        # Evaluate optimization objectives
        for obj in optimization_objectives:
            score = obj.evaluate(metrics)
            individual_scores[obj.name] = score

            if score != -float("inf"):  # Only add non-constraint-violating scores
                weighted_score = score * obj.weight
                total_score += weighted_score

        # Apply penalty for non-critical constraint violations
        non_critical_violations = len(constraint_violations) - len(critical_violations)
        if non_critical_violations > 0:
            total_score -= non_critical_violations * 0.1  # Small penalty

        return ObjectiveEvaluationResult(
            feasible=len(constraint_violations) == 0,
            total_score=total_score,
            individual_scores=individual_scores,
            constraint_violations=constraint_violations,
            optimization_method="weighted_sum",
        )

    def _lexicographic(self, metrics: Dict[str, float]) -> ObjectiveEvaluationResult:
        """Lexicographic approach - optimize by priority order."""
        # Sort objectives by priority (CRITICAL first)
        sorted_objectives = sorted(self.objectives, key=lambda x: x.priority.value)

        individual_scores = {}
        constraint_violations = []

        for obj in sorted_objectives:
            score = obj.evaluate(metrics)
            individual_scores[obj.name] = score

            # Check for constraint violations
            if obj.type == ObjectiveType.CONSTRAINT and score == -float("inf"):
                violation_msg = obj.get_violation_message(metrics)
                if violation_msg:
                    constraint_violations.append(violation_msg)

            # Critical constraint or objective failure stops optimization
            if obj.priority == ObjectivePriority.CRITICAL and score <= 0:
                return ObjectiveEvaluationResult(
                    feasible=False,
                    total_score=-float("inf"),
                    individual_scores=individual_scores,
                    constraint_violations=constraint_violations,
                    optimization_method="lexicographic",
                )

        # Primary score is highest priority non-constraint objective
        non_constraint_objectives = [obj for obj in sorted_objectives if obj.type != ObjectiveType.CONSTRAINT]
        primary_score = individual_scores[non_constraint_objectives[0].name] if non_constraint_objectives else 0.0

        return ObjectiveEvaluationResult(
            feasible=len(constraint_violations) == 0,
            total_score=primary_score,
            individual_scores=individual_scores,
            constraint_violations=constraint_violations,
            optimization_method="lexicographic",
            metadata={"priority_order": [obj.name for obj in sorted_objectives]},
        )

    def _constraint_satisfaction(self, metrics: Dict[str, float]) -> ObjectiveEvaluationResult:
        """Constraint satisfaction - feasibility first, then optimization."""
        constraints = [obj for obj in self.objectives if obj.type == ObjectiveType.CONSTRAINT]
        optimization_objectives = [obj for obj in self.objectives if obj.type != ObjectiveType.CONSTRAINT]

        # Check all constraints
        constraint_violations = []
        for constraint in constraints:
            if not constraint.is_constraint_satisfied(metrics):
                violation_msg = constraint.get_violation_message(metrics)
                if violation_msg:
                    constraint_violations.append(violation_msg)

        # If any constraints violated, system is infeasible
        if constraint_violations:
            return ObjectiveEvaluationResult(
                feasible=False,
                total_score=-float("inf"),
                individual_scores={obj.name: obj.evaluate(metrics) for obj in self.objectives},
                constraint_violations=constraint_violations,
                optimization_method="constraint_satisfaction",
            )

        # If feasible, optimize remaining objectives using weighted sum
        if optimization_objectives:
            temp_multi = MultiObjective("temp", optimization_objectives, "weighted_sum")
            result = temp_multi._weighted_sum(metrics)
            result.optimization_method = "constraint_satisfaction"

            # Add constraint scores
            for constraint in constraints:
                result.individual_scores[constraint.name] = constraint.evaluate(metrics)

            return result
        else:
            # No optimization objectives, just constraint satisfaction
            return ObjectiveEvaluationResult(
                feasible=True,
                total_score=0.0,
                individual_scores={obj.name: obj.evaluate(metrics) for obj in self.objectives},
                constraint_violations=[],
                optimization_method="constraint_satisfaction",
            )

    def _pareto_optimization(self, metrics: Dict[str, float]) -> ObjectiveEvaluationResult:
        """Pareto optimization - find trade-off solutions (placeholder for future implementation)."""
        DXA_LOGGER.warning("Pareto optimization not yet implemented, falling back to constraint satisfaction")
        return self._constraint_satisfaction(metrics)

    def get_objective_summary(self) -> Dict[str, Any]:
        """Get summary of objective configuration."""
        return {
            "name": self.name,
            "method": self.method,
            "num_objectives": len(self.objectives),
            "num_constraints": len([obj for obj in self.objectives if obj.type == ObjectiveType.CONSTRAINT]),
            "objectives": [
                {
                    "name": obj.name,
                    "type": obj.type.value,
                    "priority": obj.priority.name,
                    "weight": obj.weight,
                    "description": obj.description,
                }
                for obj in self.objectives
            ],
        }
