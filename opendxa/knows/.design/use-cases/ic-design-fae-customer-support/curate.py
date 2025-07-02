"""
Curate Phase: Knowledge Categorization and Requirements

Input: Use case (topic + procedure) + existing knowledge sources
Output: Knowledge requirements + storage structure decisions + knowledge content
"""

from typing import Any

from common.storage_types import StorageType


class CuratePhase:
    """Implements the Curate phase of the CORRAL lifecycle."""

    def __init__(self):
        self.knowledge_requirements = {}
        self.storage_decisions = {}
        self.knowledge_content = {}

    def analyze_use_case(self, use_case: dict[str, Any]) -> dict[str, Any]:
        """Analyze use case to identify knowledge requirements."""

        print("🔍 Analyzing use case requirements...")

        topic = use_case["topic"]
        procedure = use_case["procedure"]
        requirements = use_case["requirements"]

        # Map use case to knowledge requirements
        knowledge_requirements = {
            "topical_knowledge": {
                "equipment_specifications": {
                    "why_needed": "Team must select and configure vision system for non-standard fiducial patterns",
                    "use_case_impact": "Without this knowledge, they can't determine equipment capabilities, set initial parameters, or validate ±0.1mm accuracy requirements",
                    "current_gap": "Team has general equipment knowledge but lacks specific capabilities for non-standard patterns",
                },
                "material_properties": {
                    "why_needed": "High-Tg FR4 substrate has different optical properties than standard materials",
                    "use_case_impact": "Without this knowledge, they can't configure lighting for optimal fiducial detection or set contrast thresholds for reliable pattern recognition",
                    "current_gap": "Limited experience with this specific substrate material",
                },
                "calibration_standards": {
                    "why_needed": "Customer requires ±0.1mm accuracy, more stringent than typical requirements",
                    "use_case_impact": "Without this knowledge, they can't validate compliance or establish proper acceptance criteria",
                    "current_gap": "Team knows general standards but not specific requirements for this accuracy level",
                },
            },
            "procedural_knowledge": {
                "calibration_workflows": {
                    "why_needed": "Team needs systematic approach for non-standard pattern calibration",
                    "use_case_impact": "Without this knowledge, they execute calibration in wrong sequence or miss critical validation steps",
                    "current_gap": "Standard procedures don't address non-standard patterns",
                },
                "troubleshooting_procedures": {
                    "why_needed": "When calibration fails with non-standard patterns, team needs systematic troubleshooting",
                    "use_case_impact": "Without this knowledge, they repeat failed approaches and extend setup time",
                    "current_gap": "Limited experience with troubleshooting non-standard pattern issues",
                },
                "optimization_techniques": {
                    "why_needed": "Team must optimize calibration for specific customer requirements and substrate",
                    "use_case_impact": "Without this knowledge, they can't achieve ±0.1mm accuracy efficiently",
                    "current_gap": "No systematic approach to parameter optimization for unique requirements",
                },
            },
        }

        self.knowledge_requirements = knowledge_requirements
        print(
            f"✅ Identified {len(knowledge_requirements['topical_knowledge'])} topical and {len(knowledge_requirements['procedural_knowledge'])} procedural knowledge areas"
        )

        return knowledge_requirements

    def determine_storage_structures(self, knowledge_requirements: dict[str, Any]) -> dict[str, StorageType]:
        """Determine optimal storage structures for each knowledge type."""

        print("🗂️  Determining storage structures...")

        storage_decisions = {
            # Topical Knowledge
            "equipment_specifications": StorageType.RELATIONAL,
            "material_properties": StorageType.VECTOR,
            "calibration_standards": StorageType.SEMI_STRUCTURED,
            # Procedural Knowledge
            "calibration_workflows": StorageType.SEMI_STRUCTURED,
            "troubleshooting_procedures": StorageType.TIME_SERIES,
            "optimization_techniques": StorageType.VECTOR,
        }

        self.storage_decisions = storage_decisions

        # Print storage decisions with rationale
        for knowledge_type, storage_type in storage_decisions.items():
            rationale = self._get_storage_rationale(knowledge_type, storage_type)
            print(f"  {knowledge_type}: {storage_type.value} - {rationale}")

        return storage_decisions

    def generate_knowledge_content(self, knowledge_requirements: dict[str, Any]) -> dict[str, Any]:
        """Generate knowledge content for each requirement."""

        print("📝 Generating knowledge content...")

        knowledge_content = {
            "equipment_specifications": {
                "content": "Vision systems supporting ±0.1mm accuracy for BGA packages with non-standard fiducial patterns",
                "confidence": 0.9,
                "source_authority": 0.95,
                "scope": ["vision_systems", "bga_packages", "high_accuracy"],
            },
            "material_properties": {
                "content": "High-Tg FR4 optical properties: reflectivity 0.3, contrast ratio 2.5, optimal lighting wavelength 650nm",
                "confidence": 0.7,
                "source_authority": 0.8,
                "scope": ["high_tg_fr4", "optical_properties", "substrate_materials"],
            },
            "calibration_standards": {
                "content": "Industry standards for ±0.1mm accuracy: ISO 9001 compliance, statistical process control, validation procedures",
                "confidence": 0.8,
                "source_authority": 0.9,
                "scope": ["calibration_standards", "iso_9001", "statistical_control"],
            },
            "calibration_workflows": {
                "content": "Step-by-step calibration workflow for non-standard fiducial patterns with validation checkpoints",
                "confidence": 0.8,
                "source_authority": 0.85,
                "scope": ["calibration_workflows", "non_standard_patterns", "validation"],
            },
            "troubleshooting_procedures": {
                "content": "Systematic troubleshooting approach for calibration failures with root cause analysis",
                "confidence": 0.6,
                "source_authority": 0.7,
                "scope": ["troubleshooting", "calibration_failures", "root_cause_analysis"],
            },
            "optimization_techniques": {
                "content": "Parameter optimization techniques for achieving ±0.1mm accuracy with High-Tg FR4 substrates",
                "confidence": 0.75,
                "source_authority": 0.8,
                "scope": ["parameter_optimization", "high_accuracy", "substrate_optimization"],
            },
        }

        self.knowledge_content = knowledge_content
        print(f"✅ Generated knowledge content for {len(knowledge_content)} knowledge areas")

        return knowledge_content

    def _get_storage_rationale(self, knowledge_type: str, storage_type: StorageType) -> str:
        """Get rationale for storage type decision."""

        rationales = {
            "equipment_specifications": "Fast lookup for exact specifications and capabilities",
            "material_properties": "Similarity search for materials with similar optical properties",
            "calibration_standards": "Complex regulatory documents with hierarchical requirements",
            "calibration_workflows": "Workflows with conditional logic and branching",
            "troubleshooting_procedures": "Track calibration attempts over time for pattern recognition",
            "optimization_techniques": "Find similar optimization approaches quickly",
        }

        return rationales.get(knowledge_type, "Standard storage for this knowledge type")
