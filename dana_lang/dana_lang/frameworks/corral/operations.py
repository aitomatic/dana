"""CORRAL operation results and data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .knowledge import Knowledge


@dataclass
class CurationResult:
    """Result of knowledge curation operation."""

    curated_knowledge: list[Knowledge]
    quality_scores: dict[str, float]
    processing_recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def knowledge_count(self) -> int:
        return len(self.curated_knowledge)

    @property
    def average_quality(self) -> float:
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores.values()) / len(self.quality_scores)


@dataclass
class CrossReference:
    """Cross-reference between knowledge items."""

    from_knowledge_id: str
    to_knowledge_id: str
    relationship_type: str
    strength: float


@dataclass
class OrganizationResult:
    """Result of knowledge organization operation."""

    structured_knowledge: list[Knowledge]
    knowledge_graph: dict[str, list[str]]  # Adjacency list representation
    cross_references: list[CrossReference]
    indices_created: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RankedKnowledge:
    """Knowledge item with relevance ranking."""

    knowledge: Knowledge
    relevance_score: float
    ranking_factors: dict[str, float] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result of knowledge retrieval operation."""

    ranked_knowledge: list[RankedKnowledge]
    total_candidates: int
    retrieval_confidence: float
    retrieval_metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def knowledge_items(self) -> list[Knowledge]:
        return [rk.knowledge for rk in self.ranked_knowledge]

    @property
    def top_knowledge(self) -> Knowledge | None:
        return self.ranked_knowledge[0].knowledge if self.ranked_knowledge else None


@dataclass
class ReasoningTrace:
    """Trace of reasoning steps."""

    step_number: int
    operation: str
    inputs: list[str]
    outputs: list[str]
    confidence: float
    reasoning_type: str


@dataclass
class KnowledgeGap:
    """Identified gap in knowledge."""

    gap_type: str
    description: str
    priority: float
    suggested_sources: list[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """Result of knowledge reasoning operation."""

    conclusions: list[str]
    confidence_scores: dict[str, float]
    reasoning_traces: list[ReasoningTrace]
    knowledge_gaps: list[KnowledgeGap]
    insights: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def primary_conclusion(self) -> str | None:
        return self.conclusions[0] if self.conclusions else None

    @property
    def overall_confidence(self) -> float:
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)


@dataclass
class ExecutedAction:
    """Record of executed action."""

    action_type: str
    action_name: str
    parameters: dict[str, Any]
    result: Any
    success: bool
    execution_time: float


@dataclass
class ActionResult:
    """Result of knowledge-based action operation."""

    executed_actions: list[ExecutedAction]
    outcomes: list[Any]
    success_rate: float
    performance_metrics: dict[str, float] = field(default_factory=dict)
    side_effects: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_actions(self) -> int:
        return len(self.executed_actions)

    @property
    def successful_actions(self) -> int:
        return sum(1 for action in self.executed_actions if action.success)


@dataclass
class LearningUpdate:
    """Update to knowledge from learning."""

    knowledge_id: str
    update_type: str  # confidence_update, content_modification, relationship_change
    old_value: Any
    new_value: Any
    evidence: str
    confidence_change: float


@dataclass
class NewPattern:
    """Newly discovered pattern."""

    pattern_type: str
    description: str
    confidence: float
    supporting_instances: list[str]
    potential_applications: list[str]


@dataclass
class LearningResult:
    """Result of learning from outcomes."""

    knowledge_updates: list[LearningUpdate]
    new_patterns: list[NewPattern]
    confidence_improvements: dict[str, float]
    knowledge_removals: list[str]  # IDs of knowledge marked for removal
    insights: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_updates(self) -> int:
        return len(self.knowledge_updates)

    @property
    def patterns_discovered(self) -> int:
        return len(self.new_patterns)


@dataclass
class CORRALResult:
    """Complete result of CORRAL cycle execution."""

    problem_statement: str
    curation_result: CurationResult
    organization_result: OrganizationResult
    retrieval_result: RetrievalResult
    reasoning_result: ReasoningResult
    action_result: ActionResult
    learning_result: LearningResult
    cycle_success: bool
    total_execution_time: float
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def knowledge_gained(self) -> list[Knowledge]:
        """All new knowledge gained in this cycle."""
        return self.curation_result.curated_knowledge

    @property
    def confidence_changes(self) -> dict[str, float]:
        """All confidence changes in this cycle."""
        return self.learning_result.confidence_improvements

    @property
    def success_metrics(self) -> dict[str, float]:
        """Key success metrics from the cycle."""
        return {
            "cycle_success": float(self.cycle_success),
            "knowledge_quality": self.curation_result.average_quality,
            "reasoning_confidence": self.reasoning_result.overall_confidence,
            "action_success_rate": self.action_result.success_rate,
            "knowledge_updates": float(self.learning_result.total_updates),
            "patterns_discovered": float(self.learning_result.patterns_discovered),
        }
