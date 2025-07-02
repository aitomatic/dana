"""
Learn Phase: Outcome Analysis and Knowledge Evolution

Input: Execution results + performance metrics
Output: Updated knowledge base + learning outcomes
"""

import uuid
from datetime import datetime
from typing import Any

from common.knowledge_units import KnowledgeUnit, P_T_Classification, Phase, SourceType, Type


class LearnPhase:
    """Implements the Learn phase of the CORRAL lifecycle."""

    def __init__(self):
        self.last_learning = {}
        self.learning_strategy = "outcome_driven"

    def analyze_outcomes(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Analyze execution outcomes to extract learning."""

        print("📈 Analyzing execution outcomes for learning...")

        # Extract key outcomes
        overall_success = execution_results.get("overall_success", False)
        performance_metrics = execution_results.get("performance_metrics", {})
        action_results = execution_results.get("action_results", [])
        lessons_learned = execution_results.get("lessons_learned", [])

        print(f"Overall success: {overall_success}")
        print(f"Success rate: {performance_metrics.get('overall_success_rate', 0):.2f}")

        # Analyze outcomes for learning opportunities
        learning_outcomes = {
            "success_patterns": self._identify_success_patterns(action_results),
            "failure_patterns": self._identify_failure_patterns(action_results),
            "optimization_insights": self._extract_optimization_insights(action_results),
            "performance_improvements": self._analyze_performance_improvements(performance_metrics),
            "knowledge_gaps": self._identify_knowledge_gaps(action_results),
            "synthetic_knowledge": self._generate_synthetic_knowledge(execution_results),
        }

        # Create learning summary
        learning_summary = {
            "execution_id": str(uuid.uuid4()),
            "analysis_time": datetime.now(),
            "overall_success": overall_success,
            "learning_outcomes": learning_outcomes,
            "knowledge_evolution_plan": self._create_knowledge_evolution_plan(learning_outcomes),
            "continuous_improvement_loop": self._design_improvement_loop(learning_outcomes),
        }

        self.last_learning = learning_summary
        print("✅ Outcome analysis completed")

        return learning_summary

    def update_knowledge_base(self, knowledge_base: dict[str, Any], learning_outcomes: dict[str, Any]) -> dict[str, Any]:
        """Update knowledge base with learning outcomes."""

        print("🔄 Updating knowledge base with learning outcomes...")

        # Extract learning outcomes
        success_patterns = learning_outcomes.get("success_patterns", [])
        failure_patterns = learning_outcomes.get("failure_patterns", [])
        optimization_insights = learning_outcomes.get("optimization_insights", [])
        synthetic_knowledge = learning_outcomes.get("synthetic_knowledge", [])

        # Create new knowledge units from learning
        new_units = []
        promoted_units = []

        # Generate new knowledge from success patterns
        for pattern in success_patterns:
            new_unit = self._create_knowledge_unit_from_pattern(pattern, "success")
            new_units.append(new_unit)

        # Generate new knowledge from failure patterns
        for pattern in failure_patterns:
            new_unit = self._create_knowledge_unit_from_pattern(pattern, "failure")
            new_units.append(new_unit)

        # Generate new knowledge from optimization insights
        for insight in optimization_insights:
            new_unit = self._create_knowledge_unit_from_insight(insight)
            new_units.append(new_unit)

        # Generate synthetic knowledge
        for synthetic in synthetic_knowledge:
            new_unit = self._create_synthetic_knowledge_unit(synthetic)
            new_units.append(new_unit)

        # Promote existing knowledge units based on success
        promoted_units = self._promote_knowledge_units(knowledge_base, learning_outcomes)

        # Add new units to knowledge base
        for unit in new_units:
            knowledge_base["units"][unit.id] = unit
            print(f"  Added new knowledge unit: {unit.metadata['knowledge_type']}")

        # Update promoted units
        for unit in promoted_units:
            unit.promote_status("validated")
            unit.update_confidence(min(unit.confidence + 0.1, 1.0))
            print(f"  Promoted knowledge unit: {unit.metadata['knowledge_type']}")

        # Update learning summary
        self.last_learning.update(
            {"new_units": new_units, "promoted_units": promoted_units, "knowledge_base_size": len(knowledge_base["units"])}
        )

        print(f"✅ Knowledge base updated: {len(new_units)} new units, {len(promoted_units)} promoted")

        return knowledge_base

    def _identify_success_patterns(self, action_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify patterns in successful actions."""

        success_patterns = []
        successful_actions = [r for r in action_results if r["status"] == "completed"]

        for action in successful_actions:
            pattern = {
                "action_type": action["action"],
                "success_factors": action.get("optimizations_applied", []),
                "performance_metrics": {"setup_time": action["setup_time"], "accuracy": action["accuracy"]},
                "context": action.get("notes", ""),
                "confidence": 0.8,  # High confidence for successful patterns
            }
            success_patterns.append(pattern)

        return success_patterns

    def _identify_failure_patterns(self, action_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify patterns in failed actions."""

        failure_patterns = []
        failed_actions = [r for r in action_results if r["status"] == "failed"]

        for action in failed_actions:
            pattern = {
                "action_type": action["action"],
                "failure_factors": action.get("challenges", []),
                "performance_metrics": {"setup_time": action["setup_time"], "accuracy": action["accuracy"]},
                "context": action.get("notes", ""),
                "mitigation_strategies": self._generate_mitigation_strategies(action),
                "confidence": 0.7,  # Medium confidence for failure patterns
            }
            failure_patterns.append(pattern)

        return failure_patterns

    def _extract_optimization_insights(self, action_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract insights from optimization attempts."""

        optimization_insights = []

        for action in action_results:
            optimizations = action.get("optimizations_applied", [])
            if optimizations:
                insight = {
                    "action_type": action["action"],
                    "optimizations": optimizations,
                    "effectiveness": "high" if action["status"] == "completed" else "low",
                    "performance_impact": {"setup_time": action["setup_time"], "accuracy": action["accuracy"]},
                    "context": action.get("notes", ""),
                    "confidence": 0.75,
                }
                optimization_insights.append(insight)

        return optimization_insights

    def _analyze_performance_improvements(self, performance_metrics: dict[str, Any]) -> dict[str, Any]:
        """Analyze performance improvements from execution."""

        improvements = {
            "setup_time_efficiency": "improved" if performance_metrics.get("total_setup_time", 0) < 8.0 else "needs_improvement",
            "accuracy_achievement": "achieved" if "±0.1" in str(performance_metrics.get("average_accuracy", "")) else "below_target",
            "optimization_effectiveness": performance_metrics.get("optimization_effectiveness", 0),
            "success_rate": performance_metrics.get("overall_success_rate", 0),
            "recommendations": self._generate_performance_recommendations(performance_metrics),
        }

        return improvements

    def _identify_knowledge_gaps(self, action_results: list[dict[str, Any]]) -> list[str]:
        """Identify knowledge gaps revealed by execution."""

        gaps = []

        # Analyze failed actions for knowledge gaps
        failed_actions = [r for r in action_results if r["status"] == "failed"]
        for action in failed_actions:
            challenges = action.get("challenges", [])
            for challenge in challenges:
                if "substrate" in challenge.lower():
                    gaps.append("Enhanced substrate material knowledge needed")
                elif "pattern" in challenge.lower():
                    gaps.append("Non-standard pattern recognition expertise needed")
                elif "optimization" in challenge.lower():
                    gaps.append("Advanced parameter optimization techniques needed")

        # Identify gaps based on missing optimizations
        actions_without_optimizations = [r for r in action_results if not r.get("optimizations_applied")]
        if actions_without_optimizations:
            gaps.append("Optimization knowledge gaps for standard procedures")

        return list(set(gaps))  # Remove duplicates

    def _generate_synthetic_knowledge(self, execution_results: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate synthetic knowledge from execution results."""

        synthetic_knowledge = []

        # Generate knowledge from successful combinations
        successful_actions = [r for r in execution_results.get("action_results", []) if r["status"] == "completed"]
        if len(successful_actions) >= 2:
            synthetic = {
                "knowledge_type": "successful_workflow_combination",
                "content": f"Combination of {len(successful_actions)} successful actions achieved {execution_results.get('performance_metrics', {}).get('average_accuracy', 'target accuracy')}",
                "confidence": 0.8,
                "source_authority": 0.7,
                "scope": ["workflow_optimization", "success_patterns"],
            }
            synthetic_knowledge.append(synthetic)

        # Generate knowledge from performance insights
        performance_metrics = execution_results.get("performance_metrics", {})
        if performance_metrics.get("optimization_effectiveness", 0) > 0.5:
            synthetic = {
                "knowledge_type": "optimization_effectiveness",
                "content": f"Optimization techniques improved performance by {performance_metrics['optimization_effectiveness'] * 100:.1f}%",
                "confidence": 0.75,
                "source_authority": 0.8,
                "scope": ["optimization", "performance_improvement"],
            }
            synthetic_knowledge.append(synthetic)

        return synthetic_knowledge

    def _create_knowledge_unit_from_pattern(self, pattern: dict[str, Any], pattern_type: str) -> KnowledgeUnit:
        """Create knowledge unit from success/failure pattern."""

        if pattern_type == "success":
            content = f"Successful pattern: {pattern['action_type']} with factors: {', '.join(pattern['success_factors'])}"
            knowledge_type = "success_pattern"
            confidence = pattern["confidence"]
        else:
            content = f"Failure pattern: {pattern['action_type']} with challenges: {', '.join(pattern['failure_factors'])}"
            knowledge_type = "failure_pattern"
            confidence = pattern["confidence"]

        return KnowledgeUnit(
            id=str(uuid.uuid4()),
            content=content,
            p_t_classification=P_T_Classification(Phase.EXPERIENTIAL, Type.PROCEDURAL),
            source_type=SourceType.COMPUTED,
            source_authority=0.8,
            confidence=confidence,
            scope=["pattern_recognition", "execution_learning"],
            status="raw",
            usage_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"knowledge_type": knowledge_type, "pattern_type": pattern_type, "source": "execution_analysis"},
        )

    def _create_knowledge_unit_from_insight(self, insight: dict[str, Any]) -> KnowledgeUnit:
        """Create knowledge unit from optimization insight."""

        content = f"Optimization insight: {insight['action_type']} with {insight['effectiveness']} effectiveness using {', '.join(insight['optimizations'])}"

        return KnowledgeUnit(
            id=str(uuid.uuid4()),
            content=content,
            p_t_classification=P_T_Classification(Phase.EXPERIENTIAL, Type.PROCEDURAL),
            source_type=SourceType.COMPUTED,
            source_authority=0.75,
            confidence=insight["confidence"],
            scope=["optimization", "performance_improvement"],
            status="raw",
            usage_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"knowledge_type": "optimization_insight", "effectiveness": insight["effectiveness"], "source": "execution_analysis"},
        )

    def _create_synthetic_knowledge_unit(self, synthetic: dict[str, Any]) -> KnowledgeUnit:
        """Create knowledge unit from synthetic knowledge."""

        return KnowledgeUnit(
            id=str(uuid.uuid4()),
            content=synthetic["content"],
            p_t_classification=P_T_Classification(Phase.EXPERIENTIAL, Type.TOPICAL),
            source_type=SourceType.GENERATED,
            source_authority=synthetic["source_authority"],
            confidence=synthetic["confidence"],
            scope=synthetic["scope"],
            status="raw",
            usage_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"knowledge_type": synthetic["knowledge_type"], "source": "synthetic_generation"},
        )

    def _promote_knowledge_units(self, knowledge_base: dict[str, Any], learning_outcomes: dict[str, Any]) -> list[KnowledgeUnit]:
        """Promote existing knowledge units based on success."""

        promoted_units = []

        # Find units that contributed to success
        success_patterns = learning_outcomes.get("success_patterns", [])
        for pattern in success_patterns:
            # Find related knowledge units
            for unit in knowledge_base["units"].values():
                if unit.metadata["knowledge_type"] in pattern["action_type"] or any(
                    factor in unit.content for factor in pattern["success_factors"]
                ):
                    promoted_units.append(unit)

        return list(set(promoted_units))  # Remove duplicates

    def _generate_mitigation_strategies(self, action: dict[str, Any]) -> list[str]:
        """Generate mitigation strategies for failed actions."""

        strategies = []
        challenges = action.get("challenges", [])

        for challenge in challenges:
            if "substrate" in challenge.lower():
                strategies.append("Enhanced substrate material analysis")
            elif "pattern" in challenge.lower():
                strategies.append("Advanced pattern recognition algorithms")
            elif "optimization" in challenge.lower():
                strategies.append("Iterative parameter optimization")
            else:
                strategies.append("Consult with domain experts")

        return strategies

    def _generate_performance_recommendations(self, performance_metrics: dict[str, Any]) -> list[str]:
        """Generate performance improvement recommendations."""

        recommendations = []

        if performance_metrics.get("total_setup_time", 0) > 8.0:
            recommendations.append("Optimize setup procedures to reduce time")

        if performance_metrics.get("optimization_effectiveness", 0) < 0.5:
            recommendations.append("Increase use of optimization techniques")

        if performance_metrics.get("overall_success_rate", 0) < 0.8:
            recommendations.append("Review and improve action execution strategies")

        return recommendations

    def _create_knowledge_evolution_plan(self, learning_outcomes: dict[str, Any]) -> dict[str, Any]:
        """Create plan for knowledge evolution."""

        return {
            "short_term": [
                "Validate new experiential knowledge units",
                "Promote successful patterns to validated status",
                "Address identified knowledge gaps",
            ],
            "medium_term": [
                "Integrate optimization insights into workflows",
                "Develop synthetic knowledge for similar scenarios",
                "Establish continuous learning feedback loops",
            ],
            "long_term": [
                "Build comprehensive pattern recognition system",
                "Create predictive knowledge generation",
                "Implement cross-domain knowledge sharing",
            ],
        }

    def _design_improvement_loop(self, learning_outcomes: dict[str, Any]) -> dict[str, Any]:
        """Design continuous improvement loop."""

        return {
            "feedback_mechanism": "Real-time execution outcome analysis",
            "learning_triggers": ["Performance below targets", "New failure patterns identified", "Optimization opportunities discovered"],
            "improvement_actions": [
                "Update knowledge base with new insights",
                "Promote successful patterns",
                "Generate synthetic knowledge",
                "Refine optimization strategies",
            ],
            "success_metrics": ["Knowledge base growth rate", "Pattern recognition accuracy", "Performance improvement trends"],
        }
