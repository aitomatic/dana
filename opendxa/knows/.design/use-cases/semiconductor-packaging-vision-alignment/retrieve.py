"""
Retrieve Phase: Knowledge Selection and Retrieval

Input: Current task + knowledge base
Output: Selected knowledge units for reasoning
"""

from typing import Any

from common.knowledge_units import KnowledgeUnit, Phase, Type


class RetrievePhase:
    """Implements the Retrieve phase of the CORRAL lifecycle."""

    def __init__(self):
        self.last_retrieval = []
        self.retrieval_strategy = "task_driven"

    def select_knowledge(self, current_task: str, knowledge_base: dict[str, Any]) -> list[KnowledgeUnit]:
        """Select relevant knowledge for the current task."""

        print("🔍 Selecting knowledge for current task...")
        print(f"Task: {current_task}")

        # Analyze task to determine knowledge needs
        task_analysis = self._analyze_task(current_task)
        print(f"Task analysis: {task_analysis}")

        # Select knowledge based on task analysis
        selected_units = self._select_by_task_analysis(task_analysis, knowledge_base)

        # Rank and filter knowledge units
        ranked_units = self._rank_knowledge_units(selected_units, current_task)

        # Apply context window optimization
        optimized_units = self._optimize_context_window(ranked_units, current_task)

        self.last_retrieval = optimized_units
        print(f"✅ Selected {len(optimized_units)} knowledge units for reasoning")

        return optimized_units

    def _analyze_task(self, task: str) -> dict[str, Any]:
        """Analyze task to determine knowledge requirements."""

        task_lower = task.lower()

        analysis = {"knowledge_types": [], "phases": [], "types": [], "scope_keywords": [], "priority": "high"}

        # Determine knowledge types needed
        if "calibrate" in task_lower and "vision" in task_lower:
            analysis["knowledge_types"].extend(["equipment_specifications", "calibration_workflows", "calibration_standards"])

        if "non-standard" in task_lower or "fiducial" in task_lower:
            analysis["knowledge_types"].extend(["material_properties", "optimization_techniques"])

        if "bga" in task_lower or "package" in task_lower:
            analysis["knowledge_types"].append("equipment_specifications")

        # Determine phases needed
        analysis["phases"] = [Phase.DOCUMENTARY, Phase.PRIOR, Phase.EXPERIENTIAL]

        # Determine types needed
        analysis["types"] = [Type.TOPICAL, Type.PROCEDURAL]

        # Extract scope keywords
        scope_keywords = []
        if "calibration" in task_lower:
            scope_keywords.append("calibration_workflows")
        if "vision" in task_lower:
            scope_keywords.extend(["vision_systems", "high_accuracy"])
        if "bga" in task_lower:
            scope_keywords.append("bga_packages")
        if "non-standard" in task_lower:
            scope_keywords.append("non_standard_patterns")

        analysis["scope_keywords"] = scope_keywords

        return analysis

    def _select_by_task_analysis(self, task_analysis: dict[str, Any], knowledge_base: dict[str, Any]) -> list[KnowledgeUnit]:
        """Select knowledge units based on task analysis."""

        selected_units = []

        # Get all knowledge units
        all_units = list(knowledge_base["units"].values())

        for unit in all_units:
            score = 0

            # Score by knowledge type
            if unit.metadata["knowledge_type"] in task_analysis["knowledge_types"]:
                score += 10

            # Score by phase
            if unit.p_t_classification.phase in task_analysis["phases"]:
                score += 5

            # Score by type
            if unit.p_t_classification.type in task_analysis["types"]:
                score += 5

            # Score by scope overlap
            scope_overlap = len(set(unit.scope) & set(task_analysis["scope_keywords"]))
            score += scope_overlap * 3

            # Score by confidence
            score += unit.confidence * 5

            # Score by usage (prefer proven knowledge)
            score += min(unit.usage_count * 0.5, 5)

            # Only include units with meaningful relevance
            if score >= 5:
                unit.metadata["retrieval_score"] = score
                selected_units.append(unit)

        return selected_units

    def _rank_knowledge_units(self, units: list[KnowledgeUnit], task: str) -> list[KnowledgeUnit]:
        """Rank knowledge units by relevance to task."""

        # Sort by retrieval score (descending)
        ranked_units = sorted(units, key=lambda u: u.metadata.get("retrieval_score", 0), reverse=True)

        print("📊 Knowledge unit ranking:")
        for i, unit in enumerate(ranked_units[:5]):  # Show top 5
            score = unit.metadata.get("retrieval_score", 0)
            print(f"  {i + 1}. {unit.metadata['knowledge_type']} (score: {score:.1f})")

        return ranked_units

    def _optimize_context_window(self, units: list[KnowledgeUnit], task: str) -> list[KnowledgeUnit]:
        """Optimize knowledge selection for context window efficiency."""

        # Simulate context window constraints
        max_units = 8  # Simulate reasonable context window size
        max_content_length = 2000  # Simulate token limit

        optimized_units = []
        current_length = 0

        for unit in units:
            # Estimate content length (rough approximation)
            content_length = len(unit.content) + len(str(unit.metadata))

            # Check if we can add this unit
            if len(optimized_units) < max_units and current_length + content_length < max_content_length:
                optimized_units.append(unit)
                current_length += content_length
            else:
                break

        print(f"📏 Context window optimization: {len(units)} → {len(optimized_units)} units")
        print(f"📏 Estimated content length: {current_length} characters")

        return optimized_units

    def get_retrieval_explanation(self) -> str:
        """Get explanation of retrieval decisions."""

        if not self.last_retrieval:
            return "No knowledge retrieved."

        explanation = f"Retrieved {len(self.last_retrieval)} knowledge units:\n"

        for i, unit in enumerate(self.last_retrieval, 1):
            score = unit.metadata.get("retrieval_score", 0)
            explanation += f"{i}. {unit.metadata['knowledge_type']} "
            explanation += f"({unit.p_t_classification.phase.value} + {unit.p_t_classification.type.value}) "
            explanation += f"[score: {score:.1f}]\n"

        return explanation

    def get_knowledge_gaps(self, task: str, retrieved_units: list[KnowledgeUnit]) -> list[str]:
        """Identify knowledge gaps for the current task."""

        gaps = []

        # Check for missing knowledge types
        task_analysis = self._analyze_task(task)
        retrieved_types = [unit.metadata["knowledge_type"] for unit in retrieved_units]

        for required_type in task_analysis["knowledge_types"]:
            if required_type not in retrieved_types:
                gaps.append(f"Missing {required_type} knowledge")

        # Check for low confidence knowledge
        low_confidence_units = [u for u in retrieved_units if u.confidence < 0.7]
        if low_confidence_units:
            gaps.append(f"{len(low_confidence_units)} units have low confidence (< 0.7)")

        # Check for missing experiential knowledge
        experiential_units = [u for u in retrieved_units if u.p_t_classification.phase == Phase.EXPERIENTIAL]
        if len(experiential_units) < 2:
            gaps.append("Limited experiential knowledge available")

        return gaps
