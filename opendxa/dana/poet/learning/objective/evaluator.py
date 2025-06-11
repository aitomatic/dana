"""
Objective Evaluator

Runtime evaluator that integrates with POET execution pipeline to evaluate
objectives and guide learning decisions based on formal learning theory.
"""

from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass

from .base import MultiObjective, ObjectiveEvaluationResult
from .registry import get_global_registry
from opendxa.common.utils.logging import DXA_LOGGER


@dataclass
class EvaluationContext:
    """Context information for objective evaluation."""

    domain: str
    function_name: str
    execution_id: str
    timestamp: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


class ObjectiveEvaluator:
    """
    Runtime objective evaluator for POET learning systems.

    Integrates with POET execution pipeline to evaluate objectives and provide
    learning guidance based on formal multi-objective optimization.
    """

    def __init__(self, registry=None):
        self.registry = registry or get_global_registry()
        self._evaluation_history: List[Tuple[EvaluationContext, ObjectiveEvaluationResult]] = []
        self._max_history_size = 1000  # Keep last 1000 evaluations

    def evaluate_execution(
        self, domain: str, metrics: Dict[str, float], context: Optional[EvaluationContext] = None, **objective_config
    ) -> ObjectiveEvaluationResult:
        """
        Evaluate execution metrics against domain objectives.

        Args:
            domain: Domain name (e.g., "building_management")
            metrics: Execution metrics to evaluate
            context: Optional evaluation context
            **objective_config: Domain-specific objective configuration

        Returns:
            ObjectiveEvaluationResult: Evaluation result with scores and constraints
        """
        try:
            # Get domain objectives
            multi_objective = self.registry.get_domain_objectives(domain, **objective_config)

            # Evaluate objectives
            result = multi_objective.evaluate(metrics)

            # Add context information
            if context:
                result.metadata.update(
                    {
                        "domain": domain,
                        "function_name": context.function_name,
                        "execution_id": context.execution_id,
                        "evaluation_timestamp": context.timestamp,
                    }
                )

            # Store in history
            if context:
                self._store_evaluation(context, result)

            # Log evaluation results
            self._log_evaluation_result(domain, result, metrics)

            return result

        except Exception as e:
            DXA_LOGGER.error(f"Objective evaluation failed for domain {domain}: {e}")
            return ObjectiveEvaluationResult(
                feasible=False,
                total_score=-float("inf"),
                individual_scores={},
                constraint_violations=[f"Evaluation error: {str(e)}"],
                optimization_method="error",
            )

    def should_adjust_parameters(self, domain: str, current_metrics: Dict[str, float], **objective_config) -> Dict[str, Any]:
        """
        Determine if parameter adjustment is needed based on objective evaluation.

        Args:
            domain: Domain name
            current_metrics: Current execution metrics
            **objective_config: Domain-specific objective configuration

        Returns:
            Dict: Adjustment recommendations with reasoning
        """
        result = self.evaluate_execution(domain, current_metrics, **objective_config)

        recommendations = {
            "should_adjust": False,
            "reason": "No adjustment needed",
            "priority": "low",
            "suggested_changes": [],
            "constraint_violations": result.constraint_violations,
            "feasible": result.feasible,
        }

        # Critical constraint violations - immediate adjustment needed
        if not result.feasible and result.constraint_violations:
            critical_violations = self._identify_critical_violations(result.constraint_violations)
            if critical_violations:
                recommendations.update(
                    {
                        "should_adjust": True,
                        "reason": f"Critical constraint violations: {critical_violations}",
                        "priority": "critical",
                        "suggested_changes": self._suggest_constraint_fixes(critical_violations),
                    }
                )
                return recommendations

        # Performance optimization opportunities
        if result.feasible and result.total_score < 0.7:  # Below good performance threshold
            recommendations.update(
                {
                    "should_adjust": True,
                    "reason": f"Performance score {result.total_score:.3f} below target (0.7)",
                    "priority": "medium",
                    "suggested_changes": self._suggest_performance_improvements(result),
                }
            )

        # Historical trend analysis
        trend_analysis = self._analyze_performance_trend(domain)
        if trend_analysis["declining"]:
            recommendations.update(
                {
                    "should_adjust": True,
                    "reason": f"Performance declining: {trend_analysis['trend_description']}",
                    "priority": "high",
                    "suggested_changes": self._suggest_trend_corrections(trend_analysis),
                }
            )

        return recommendations

    def get_learning_guidance(self, domain: str, execution_history: List[Dict[str, float]], **objective_config) -> Dict[str, Any]:
        """
        Provide learning guidance based on objective evaluation history.

        Args:
            domain: Domain name
            execution_history: List of historical execution metrics
            **objective_config: Domain-specific objective configuration

        Returns:
            Dict: Learning guidance with parameter suggestions and priorities
        """
        if not execution_history:
            return {"guidance": "No execution history available", "parameter_suggestions": {}, "learning_priorities": []}

        # Evaluate recent performance
        recent_evaluations = []
        for metrics in execution_history[-10:]:  # Last 10 executions
            result = self.evaluate_execution(domain, metrics, **objective_config)
            recent_evaluations.append((metrics, result))

        # Analyze patterns
        guidance = {
            "guidance": self._generate_learning_guidance(recent_evaluations),
            "parameter_suggestions": self._suggest_parameter_adjustments(recent_evaluations),
            "learning_priorities": self._identify_learning_priorities(recent_evaluations),
            "objective_weights": self._suggest_objective_weight_adjustments(recent_evaluations),
            "constraint_analysis": self._analyze_constraint_patterns(recent_evaluations),
        }

        return guidance

    def validate_metrics(self, domain: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate metrics against domain requirements.

        Args:
            domain: Domain name
            metrics: Metrics to validate

        Returns:
            Dict: Validation result
        """
        return self.registry.validate_metrics_for_domain(domain, metrics)

    def get_domain_summary(self, domain: str) -> Dict[str, Any]:
        """Get summary of domain objectives and evaluation history."""
        summary = self.registry.get_domain_summary(domain)

        # Add evaluation history statistics
        domain_evaluations = [(ctx, result) for ctx, result in self._evaluation_history if ctx.domain == domain]

        if domain_evaluations:
            recent_scores = [result.total_score for _, result in domain_evaluations[-20:]]
            recent_feasible = [result.feasible for _, result in domain_evaluations[-20:]]

            summary["evaluation_stats"] = {
                "total_evaluations": len(domain_evaluations),
                "recent_avg_score": sum(recent_scores) / len(recent_scores) if recent_scores else 0.0,
                "recent_feasibility_rate": sum(recent_feasible) / len(recent_feasible) if recent_feasible else 0.0,
                "last_evaluation": domain_evaluations[-1][0].timestamp if domain_evaluations else None,
            }

        return summary

    def _store_evaluation(self, context: EvaluationContext, result: ObjectiveEvaluationResult):
        """Store evaluation in history with size limit."""
        self._evaluation_history.append((context, result))

        # Maintain history size limit
        if len(self._evaluation_history) > self._max_history_size:
            self._evaluation_history = self._evaluation_history[-self._max_history_size :]

    def _log_evaluation_result(self, domain: str, result: ObjectiveEvaluationResult, metrics: Dict[str, float]):
        """Log evaluation results for debugging."""
        if not result.feasible:
            DXA_LOGGER.warning(f"Domain {domain} objective evaluation failed: {result.constraint_violations}")
        elif result.total_score < 0.5:
            DXA_LOGGER.info(f"Domain {domain} low performance score: {result.total_score:.3f}")
        else:
            DXA_LOGGER.debug(f"Domain {domain} objective evaluation: score={result.total_score:.3f}, feasible={result.feasible}")

    def _identify_critical_violations(self, violations: List[str]) -> List[str]:
        """Identify critical constraint violations."""
        critical_keywords = ["safety", "critical", "compliance", "equipment"]
        return [v for v in violations if any(keyword in v.lower() for keyword in critical_keywords)]

    def _suggest_constraint_fixes(self, violations: List[str]) -> List[str]:
        """Suggest fixes for constraint violations."""
        suggestions = []
        for violation in violations:
            if "safety" in violation.lower():
                suggestions.append("Increase safety margins and reduce aggressive parameter settings")
            elif "response_time" in violation.lower():
                suggestions.append("Optimize execution pipeline and reduce timeout thresholds")
            elif "temperature" in violation.lower():
                suggestions.append("Adjust setpoint limits and thermal control parameters")
            else:
                suggestions.append(f"Review and adjust parameters related to: {violation}")
        return suggestions

    def _suggest_performance_improvements(self, result: ObjectiveEvaluationResult) -> List[str]:
        """Suggest improvements based on objective scores."""
        suggestions = []

        for obj_name, score in result.individual_scores.items():
            if score < 0.5:
                if "energy" in obj_name:
                    suggestions.append("Improve energy efficiency through better setpoint management")
                elif "comfort" in obj_name:
                    suggestions.append("Enhance comfort through more responsive control")
                elif "execution_time" in obj_name:
                    suggestions.append("Optimize execution speed through parameter tuning")
                else:
                    suggestions.append(f"Focus learning on improving {obj_name}")

        return suggestions

    def _analyze_performance_trend(self, domain: str) -> Dict[str, Any]:
        """Analyze performance trends for a domain."""
        domain_evaluations = [result for ctx, result in self._evaluation_history if ctx.domain == domain]

        if len(domain_evaluations) < 5:
            return {"declining": False, "trend_description": "Insufficient data"}

        recent_scores = [result.total_score for result in domain_evaluations[-5:]]
        older_scores = [result.total_score for result in domain_evaluations[-10:-5]] if len(domain_evaluations) >= 10 else recent_scores

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        declining = recent_avg < older_avg - 0.1  # 10% decline threshold

        return {
            "declining": declining,
            "recent_avg": recent_avg,
            "older_avg": older_avg,
            "trend_description": f"Recent: {recent_avg:.3f}, Previous: {older_avg:.3f}",
        }

    def _suggest_trend_corrections(self, trend_analysis: Dict[str, Any]) -> List[str]:
        """Suggest corrections for declining trends."""
        return [
            "Reduce learning rate to stabilize performance",
            "Review recent parameter changes for negative impacts",
            "Increase exploration to find better parameter regions",
            "Check for environmental changes affecting performance",
        ]

    def _generate_learning_guidance(self, evaluations: List[Tuple[Dict[str, float], ObjectiveEvaluationResult]]) -> str:
        """Generate high-level learning guidance."""
        if not evaluations:
            return "No evaluation data available"

        feasible_rate = sum(1 for _, result in evaluations if result.feasible) / len(evaluations)
        avg_score = sum(result.total_score for _, result in evaluations if result.feasible) / max(
            1, sum(1 for _, result in evaluations if result.feasible)
        )

        if feasible_rate < 0.8:
            return f"Focus on constraint satisfaction (only {feasible_rate:.1%} feasible)"
        elif avg_score < 0.6:
            return f"Optimize performance (average score: {avg_score:.3f})"
        else:
            return f"Fine-tune for excellence (current performance good: {avg_score:.3f})"

    def _suggest_parameter_adjustments(self, evaluations: List[Tuple[Dict[str, float], ObjectiveEvaluationResult]]) -> Dict[str, str]:
        """Suggest specific parameter adjustments."""
        # This would analyze the evaluations to suggest specific parameter changes
        # For now, return generic suggestions
        return {
            "learning_rate": "Consider reducing if performance is unstable",
            "exploration_rate": "Increase if performance has plateaued",
            "constraint_margins": "Increase if frequent constraint violations",
        }

    def _identify_learning_priorities(self, evaluations: List[Tuple[Dict[str, float], ObjectiveEvaluationResult]]) -> List[str]:
        """Identify learning priorities based on evaluations."""
        priorities = []

        # Analyze common patterns in poor performance
        poor_evaluations = [result for _, result in evaluations if result.total_score < 0.6]
        if poor_evaluations:
            priorities.append("Improve overall performance optimization")

        # Check for constraint violations
        violation_rate = sum(1 for _, result in evaluations if not result.feasible) / len(evaluations)
        if violation_rate > 0.2:
            priorities.append("Focus on constraint satisfaction")

        return priorities or ["Continue current learning approach"]

    def _suggest_objective_weight_adjustments(
        self, evaluations: List[Tuple[Dict[str, float], ObjectiveEvaluationResult]]
    ) -> Dict[str, float]:
        """Suggest adjustments to objective weights."""
        # For now, return default weights
        # In a full implementation, this would analyze which objectives are consistently underperforming
        return {"energy_efficiency": 0.4, "comfort_score": 0.3, "execution_time": 0.3}

    def _analyze_constraint_patterns(self, evaluations: List[Tuple[Dict[str, float], ObjectiveEvaluationResult]]) -> Dict[str, Any]:
        """Analyze patterns in constraint violations."""
        all_violations = []
        for _, result in evaluations:
            all_violations.extend(result.constraint_violations)

        if not all_violations:
            return {"status": "No constraint violations", "patterns": []}

        # Count violation types
        violation_counts = {}
        for violation in all_violations:
            violation_counts[violation] = violation_counts.get(violation, 0) + 1

        return {
            "status": f"{len(all_violations)} total violations across {len(evaluations)} evaluations",
            "patterns": violation_counts,
            "most_common": max(violation_counts.items(), key=lambda x: x[1]) if violation_counts else None,
        }
