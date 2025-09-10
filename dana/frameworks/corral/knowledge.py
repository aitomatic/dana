"""Knowledge representation and categories for the CORRAL framework."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KnowledgeCategory(Enum):
    """Primary knowledge categories in CORRAL."""

    DECLARATIVE = "declarative"  # Whats/Facts
    PROCEDURAL = "procedural"  # Hows/Methods
    CAUSAL = "causal"  # Whys/Reasoning
    RELATIONAL = "relational"  # Whos/Wheres/Structure
    CONDITIONAL = "conditional"  # Whens/Context


@dataclass
class ValidationEvent:
    """Record of knowledge validation."""

    timestamp: datetime
    validator: str
    result: bool
    confidence_change: float
    evidence: str | None = None


@dataclass
class Knowledge:
    """Base knowledge item in CORRAL system."""

    id: str
    category: KnowledgeCategory
    content: dict[str, Any]
    confidence: float
    source: str
    timestamp: datetime
    context: dict[str, Any] = field(default_factory=dict)
    validation_history: list[ValidationEvent] = field(default_factory=list)
    usage_count: int = 0
    last_accessed: datetime | None = None
    relationships: list[str] = field(default_factory=list)  # IDs of related knowledge

    def update_confidence(self, new_confidence: float, validator: str, evidence: str = None) -> None:
        """Update confidence score with validation history."""
        old_confidence = self.confidence
        self.confidence = max(0.0, min(1.0, new_confidence))  # Clamp to [0,1]

        validation = ValidationEvent(
            timestamp=datetime.now(),
            validator=validator,
            result=new_confidence >= old_confidence,
            confidence_change=self.confidence - old_confidence,
            evidence=evidence,
        )
        self.validation_history.append(validation)

    def record_access(self) -> None:
        """Record that this knowledge was accessed."""
        self.usage_count += 1
        self.last_accessed = datetime.now()

    def add_relationship(self, knowledge_id: str) -> None:
        """Add relationship to another knowledge item."""
        if knowledge_id not in self.relationships:
            self.relationships.append(knowledge_id)


@dataclass
class DeclarativeKnowledge(Knowledge):
    """Declarative knowledge: facts, entities, properties."""

    entity: str = ""
    property: str = ""
    value: Any = None

    def __post_init__(self):
        if self.category != KnowledgeCategory.DECLARATIVE:
            self.category = KnowledgeCategory.DECLARATIVE


@dataclass
class Condition:
    """Condition for procedural or conditional knowledge."""

    type: str
    expression: str
    value: Any


@dataclass
class ProcedureStep:
    """Single step in a procedure."""

    step_number: int
    action: str
    description: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)


@dataclass
class ProceduralKnowledge(Knowledge):
    """Procedural knowledge: how to do things."""

    procedure_name: str = ""
    steps: list[ProcedureStep] = field(default_factory=list)
    preconditions: list[Condition] = field(default_factory=list)
    postconditions: list[Condition] = field(default_factory=list)
    success_rate: float = 0.0
    efficiency_metrics: dict[str, float] = field(default_factory=dict)
    context_requirements: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.category != KnowledgeCategory.PROCEDURAL:
            self.category = KnowledgeCategory.PROCEDURAL


@dataclass
class Evidence:
    """Evidence supporting or refuting causal knowledge."""

    description: str
    strength: float
    source: str
    timestamp: datetime


@dataclass
class CausalKnowledge(Knowledge):
    """Causal knowledge: cause-effect relationships."""

    cause: str = ""
    effect: str = ""
    mechanism: str = ""
    conditions: list[Condition] = field(default_factory=list)
    strength: float = 0.5  # How strong the causal relationship is
    supporting_evidence: list[Evidence] = field(default_factory=list)
    counter_evidence: list[Evidence] = field(default_factory=list)

    def __post_init__(self):
        if self.category != KnowledgeCategory.CAUSAL:
            self.category = KnowledgeCategory.CAUSAL

    def add_evidence(self, evidence: Evidence, supporting: bool = True) -> None:
        """Add supporting or counter evidence."""
        if supporting:
            self.supporting_evidence.append(evidence)
        else:
            self.counter_evidence.append(evidence)


@dataclass
class RelationalKnowledge(Knowledge):
    """Relational knowledge: relationships between entities."""

    entity1: str = ""
    entity2: str = ""
    relationship_type: str = ""
    relationship_properties: dict[str, Any] = field(default_factory=dict)
    bidirectional: bool = False
    strength: float = 0.5
    context_dependent: bool = False
    temporal_aspects: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.category != KnowledgeCategory.RELATIONAL:
            self.category = KnowledgeCategory.RELATIONAL


@dataclass
class TimePeriod:
    """Time period specification."""

    start: datetime | None = None
    end: datetime | None = None
    duration: str | None = None  # Human readable duration


@dataclass
class ConditionalKnowledge(Knowledge):
    """Conditional knowledge: when other knowledge applies."""

    base_knowledge_id: str = ""
    conditions: list[Condition] = field(default_factory=list)
    context_requirements: dict[str, Any] = field(default_factory=dict)
    validity_period: TimePeriod | None = None
    confidence_modifiers: dict[str, float] = field(default_factory=dict)
    override_priority: int = 0
    application_count: int = 0

    def __post_init__(self):
        if self.category != KnowledgeCategory.CONDITIONAL:
            self.category = KnowledgeCategory.CONDITIONAL

    def applies_to_context(self, context: dict[str, Any]) -> bool:
        """Check if this conditional knowledge applies to given context."""
        # Simple implementation - would be more sophisticated in practice
        for key, required_value in self.context_requirements.items():
            if context.get(key) != required_value:
                return False
        return True


def create_knowledge(category: KnowledgeCategory, content: dict[str, Any], confidence: float, source: str, **kwargs) -> Knowledge:
    """Factory function to create appropriate knowledge type."""
    common_args = {
        "id": f"{category.value}_{datetime.now().timestamp()}",
        "category": category,
        "content": content,
        "confidence": confidence,
        "source": source,
        "timestamp": datetime.now(),
        **kwargs,
    }

    if category == KnowledgeCategory.DECLARATIVE:
        return DeclarativeKnowledge(**common_args)
    elif category == KnowledgeCategory.PROCEDURAL:
        return ProceduralKnowledge(**common_args)
    elif category == KnowledgeCategory.CAUSAL:
        return CausalKnowledge(**common_args)
    elif category == KnowledgeCategory.RELATIONAL:
        return RelationalKnowledge(**common_args)
    elif category == KnowledgeCategory.CONDITIONAL:
        return ConditionalKnowledge(**common_args)
    else:
        return Knowledge(**common_args)
