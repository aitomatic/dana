"""
Reason Phase: Knowledge Composition and Reasoning

Input: Retrieved knowledge units + current task
Output: Composed knowledge for action
"""

from typing import Any

from common.knowledge_units import KnowledgeUnit, Phase, Type


class ReasonPhase:
    """Implements the Reason phase of the CORRAL lifecycle."""

    def __init__(self):
        self.composition_strategy = "structured_reasoning"
        self.last_composition = {}

    def compose_knowledge(self, retrieved_knowledge: list[KnowledgeUnit], current_task: str) -> dict[str, Any]:
        """Compose retrieved knowledge into actionable reasoning."""

        print("🧠 Composing knowledge for reasoning...")

        # Separate knowledge by type for structured reasoning
        topical_knowledge = [u for u in retrieved_knowledge if u.p_t_classification.type == Type.TOPICAL]
        procedural_knowledge = [u for u in retrieved_knowledge if u.p_t_classification.type == Type.PROCEDURAL]

        print(f"📚 Topical knowledge: {len(topical_knowledge)} units")
        print(f"⚙️  Procedural knowledge: {len(procedural_knowledge)} units")

        # Compose knowledge using structured reasoning
        composed_knowledge = self._structured_reasoning(topical_knowledge, procedural_knowledge, current_task)

        # Generate reasoning explanation
        reasoning_explanation = self._generate_reasoning_explanation(composed_knowledge, retrieved_knowledge)

        # Create final composition
        final_composition = {
            "composed_knowledge": composed_knowledge,
            "reasoning_explanation": reasoning_explanation,
            "confidence_assessment": self._assess_confidence(composed_knowledge, retrieved_knowledge),
            "uncertainty_areas": self._identify_uncertainty_areas(composed_knowledge, retrieved_knowledge),
            "action_recommendations": self._generate_action_recommendations(composed_knowledge),
        }

        self.last_composition = final_composition
        print("✅ Knowledge composition completed")

        return final_composition

    def _structured_reasoning(
        self, topical_knowledge: list[KnowledgeUnit], procedural_knowledge: list[KnowledgeUnit], current_task: str
    ) -> dict[str, Any]:
        """Apply structured reasoning to compose knowledge."""

        composition = {
            "context_understanding": {},
            "procedural_approach": {},
            "constraints_and_requirements": {},
            "optimization_opportunities": {},
            "risk_considerations": {},
        }

        # Build context understanding from topical knowledge
        context = {}
        for unit in topical_knowledge:
            if unit.metadata["knowledge_type"] == "equipment_specifications":
                context["equipment_capabilities"] = unit.content
            elif unit.metadata["knowledge_type"] == "material_properties":
                context["substrate_characteristics"] = unit.content
            elif unit.metadata["knowledge_type"] == "calibration_standards":
                context["accuracy_requirements"] = unit.content

        composition["context_understanding"] = context

        # Build procedural approach from procedural knowledge
        procedures = {}
        for unit in procedural_knowledge:
            if unit.metadata["knowledge_type"] == "calibration_workflows":
                procedures["main_workflow"] = unit.content
            elif unit.metadata["knowledge_type"] == "troubleshooting_procedures":
                procedures["troubleshooting"] = unit.content
            elif unit.metadata["knowledge_type"] == "optimization_techniques":
                procedures["optimization"] = unit.content

        composition["procedural_approach"] = procedures

        # Extract constraints and requirements
        constraints = {
            "accuracy": "±0.1mm",
            "package_type": "BGA (324 balls, 0.4mm pitch)",
            "substrate": "High-Tg FR4",
            "volume": "10,000 units/month",
        }
        composition["constraints_and_requirements"] = constraints

        # Identify optimization opportunities
        optimizations = []
        for unit in procedural_knowledge:
            if unit.metadata["knowledge_type"] == "optimization_techniques":
                optimizations.append(
                    {"area": "parameter_optimization", "technique": unit.content, "expected_benefit": "Improved accuracy and efficiency"}
                )

        composition["optimization_opportunities"] = optimizations

        # Assess risks
        risks = [
            {
                "risk": "Non-standard fiducial pattern recognition",
                "mitigation": "Use material properties knowledge for optimal lighting configuration",
                "probability": "medium",
            },
            {
                "risk": "Achieving ±0.1mm accuracy",
                "mitigation": "Follow calibration standards and validation procedures",
                "probability": "high",
            },
            {"risk": "Substrate material variations", "mitigation": "Apply optimization techniques for High-Tg FR4", "probability": "low"},
        ]
        composition["risk_considerations"] = risks

        return composition

    def _generate_reasoning_explanation(self, composed_knowledge: dict[str, Any], retrieved_knowledge: list[KnowledgeUnit]) -> str:
        """Generate explanation of reasoning process."""

        explanation = "🧠 KNOWS Reasoning Process:\n\n"

        # Explain knowledge sources
        explanation += "📚 Knowledge Sources:\n"
        for unit in retrieved_knowledge:
            explanation += f"  • {unit.metadata['knowledge_type']} "
            explanation += f"({unit.p_t_classification.phase.value} + {unit.p_t_classification.type.value}) "
            explanation += f"[confidence: {unit.confidence:.2f}]\n"

        explanation += "\n🔍 Context Understanding:\n"
        context = composed_knowledge["context_understanding"]
        for key, value in context.items():
            explanation += f"  • {key}: {value[:100]}...\n"

        explanation += "\n⚙️  Procedural Approach:\n"
        procedures = composed_knowledge["procedural_approach"]
        for key, value in procedures.items():
            explanation += f"  • {key}: {value[:100]}...\n"

        explanation += "\n⚠️  Risk Considerations:\n"
        risks = composed_knowledge["risk_considerations"]
        for risk in risks:
            explanation += f"  • {risk['risk']} (probability: {risk['probability']})\n"

        return explanation

    def _assess_confidence(self, composed_knowledge: dict[str, Any], retrieved_knowledge: list[KnowledgeUnit]) -> dict[str, float]:
        """Assess confidence in different aspects of reasoning."""

        confidence_assessment = {
            "overall_confidence": 0.0,
            "context_confidence": 0.0,
            "procedural_confidence": 0.0,
            "constraint_confidence": 0.0,
        }

        # Calculate context confidence from topical knowledge
        topical_units = [u for u in retrieved_knowledge if u.p_t_classification.type == Type.TOPICAL]
        if topical_units:
            context_confidence = sum(u.confidence for u in topical_units) / len(topical_units)
            confidence_assessment["context_confidence"] = context_confidence

        # Calculate procedural confidence from procedural knowledge
        procedural_units = [u for u in retrieved_knowledge if u.p_t_classification.type == Type.PROCEDURAL]
        if procedural_units:
            procedural_confidence = sum(u.confidence for u in procedural_units) / len(procedural_units)
            confidence_assessment["procedural_confidence"] = procedural_confidence

        # Constraint confidence (high for well-defined requirements)
        confidence_assessment["constraint_confidence"] = 0.95

        # Overall confidence (weighted average)
        weights = [0.3, 0.4, 0.3]  # context, procedural, constraint
        confidences = [
            confidence_assessment["context_confidence"],
            confidence_assessment["procedural_confidence"],
            confidence_assessment["constraint_confidence"],
        ]
        confidence_assessment["overall_confidence"] = sum(w * c for w, c in zip(weights, confidences, strict=False))

        return confidence_assessment

    def _identify_uncertainty_areas(self, composed_knowledge: dict[str, Any], retrieved_knowledge: list[KnowledgeUnit]) -> list[str]:
        """Identify areas of uncertainty in reasoning."""

        uncertainties = []

        # Check for missing knowledge types
        knowledge_types = [u.metadata["knowledge_type"] for u in retrieved_knowledge]
        required_types = ["equipment_specifications", "calibration_workflows", "material_properties"]

        for required_type in required_types:
            if required_type not in knowledge_types:
                uncertainties.append(f"Missing {required_type} knowledge")

        # Check for low confidence knowledge
        low_confidence_units = [u for u in retrieved_knowledge if u.confidence < 0.7]
        if low_confidence_units:
            uncertainties.append(f"{len(low_confidence_units)} knowledge units have low confidence")

        # Check for limited experiential knowledge
        experiential_units = [u for u in retrieved_knowledge if u.p_t_classification.phase == Phase.EXPERIENTIAL]
        if len(experiential_units) < 2:
            uncertainties.append("Limited experiential knowledge for this specific scenario")

        # Check for non-standard pattern challenges
        if "non-standard" in str(composed_knowledge).lower():
            uncertainties.append("Non-standard fiducial patterns may require additional optimization")

        return uncertainties

    def _generate_action_recommendations(self, composed_knowledge: dict[str, Any]) -> list[dict[str, str]]:
        """Generate specific action recommendations."""

        recommendations = []

        # Equipment setup recommendation
        recommendations.append(
            {
                "action": "Configure vision system for High-Tg FR4 substrate",
                "rationale": "Material properties indicate optimal lighting wavelength of 650nm",
                "priority": "high",
            }
        )

        # Calibration workflow recommendation
        recommendations.append(
            {
                "action": "Follow non-standard pattern calibration workflow",
                "rationale": "Standard procedures don't address non-standard fiducial patterns",
                "priority": "high",
            }
        )

        # Validation recommendation
        recommendations.append(
            {
                "action": "Implement ±0.1mm accuracy validation",
                "rationale": "Customer requirement exceeds typical calibration standards",
                "priority": "critical",
            }
        )

        # Optimization recommendation
        if composed_knowledge["optimization_opportunities"]:
            recommendations.append(
                {
                    "action": "Apply parameter optimization techniques",
                    "rationale": "Optimization knowledge available for High-Tg FR4 substrates",
                    "priority": "medium",
                }
            )

        return recommendations
