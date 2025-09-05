"""Configuration for CORRAL framework."""

from dataclasses import dataclass, field
from enum import Enum


class SourceType(Enum):
    """Types of knowledge sources."""

    INTERACTION = "interaction"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    EXTERNAL = "external"
    USER_FEEDBACK = "user_feedback"


class IndexingStrategy(Enum):
    """Knowledge indexing strategies."""

    SIMPLE = "simple"
    MULTI_DIMENSIONAL = "multi_dimensional"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ReasoningType(Enum):
    """Types of reasoning supported."""

    CAUSAL = "causal"
    ANALOGICAL = "analogical"
    DEDUCTIVE = "deductive"
    ABDUCTIVE = "abductive"
    TEMPORAL = "temporal"


class ExplanationDepth(Enum):
    """Depth of explanations."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ActionMode(Enum):
    """Action execution modes."""

    INTEGRATED = "integrated"  # Through Dana workflows
    STANDALONE = "standalone"  # Direct execution


@dataclass
class CORRALConfig:
    """Configuration for CORRAL framework operations."""

    # Curation settings
    curation_sources: list[SourceType] = field(default_factory=lambda: [SourceType.INTERACTION, SourceType.WORKFLOW, SourceType.RESOURCE])
    quality_threshold: float = 0.7
    auto_validation: bool = True

    # Organization settings
    auto_categorization: bool = True
    relationship_discovery: bool = True
    indexing_strategy: IndexingStrategy = IndexingStrategy.MULTI_DIMENSIONAL

    # Retrieval settings
    max_retrieval_results: int = 10
    min_confidence_threshold: float = 0.5
    context_window: int = 5  # Number of related knowledge items to include

    # Reasoning settings
    reasoning_types: list[ReasoningType] = field(default_factory=lambda: [ReasoningType.CAUSAL, ReasoningType.ANALOGICAL])
    explanation_depth: ExplanationDepth = ExplanationDepth.STANDARD
    confidence_propagation: bool = True

    # Action settings
    action_execution_mode: ActionMode = ActionMode.INTEGRATED
    fallback_strategies: bool = True
    risk_assessment: bool = True

    # Learning settings
    learning_rate: float = 0.1
    pattern_discovery: bool = True
    knowledge_pruning: bool = True
    meta_learning: bool = True

    # Performance settings
    enable_caching: bool = True
    parallel_processing: bool = True
    max_memory_usage_mb: int = 1024

    def validate(self) -> None:
        """Validate configuration values."""
        if not 0 <= self.quality_threshold <= 1:
            raise ValueError("quality_threshold must be between 0 and 1")
        if not 0 <= self.min_confidence_threshold <= 1:
            raise ValueError("min_confidence_threshold must be between 0 and 1")
        if self.max_retrieval_results <= 0:
            raise ValueError("max_retrieval_results must be positive")
        if not 0 <= self.learning_rate <= 1:
            raise ValueError("learning_rate must be between 0 and 1")
        if self.context_window < 0:
            raise ValueError("context_window must be non-negative")


# Default configurations for different use cases
DEFAULT_CONFIG = CORRALConfig()

LIGHTWEIGHT_CONFIG = CORRALConfig(
    max_retrieval_results=5,
    reasoning_types=[ReasoningType.CAUSAL],
    explanation_depth=ExplanationDepth.MINIMAL,
    pattern_discovery=False,
    knowledge_pruning=False,
    parallel_processing=False,
    max_memory_usage_mb=256,
)

COMPREHENSIVE_CONFIG = CORRALConfig(
    max_retrieval_results=20,
    reasoning_types=[ReasoningType.CAUSAL, ReasoningType.ANALOGICAL, ReasoningType.DEDUCTIVE, ReasoningType.ABDUCTIVE],
    explanation_depth=ExplanationDepth.COMPREHENSIVE,
    context_window=10,
    learning_rate=0.2,
    max_memory_usage_mb=2048,
)
