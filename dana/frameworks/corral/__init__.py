"""CORRAL Framework - Complete Knowledge Lifecycle for Dana Agents.

The CORRAL framework implements a complete knowledge lifecycle:
Curate → Organize → Retrieve → Reason → Act → Learn

This enables Dana agents to build, maintain, and continuously improve
their knowledge through direct experience and outcome feedback.
"""

from .actor_mixin import CORRALActorMixin
from .config import CORRALConfig
from .knowledge import (
    CausalKnowledge,
    ConditionalKnowledge,
    DeclarativeKnowledge,
    Knowledge,
    KnowledgeCategory,
    ProceduralKnowledge,
    RelationalKnowledge,
)
from .operations import (
    ActionResult,
    CORRALResult,
    CurationResult,
    LearningResult,
    OrganizationResult,
    ReasoningResult,
    RetrievalResult,
)

__all__ = [
    "CORRALActorMixin",
    "Knowledge",
    "KnowledgeCategory",
    "DeclarativeKnowledge",
    "ProceduralKnowledge",
    "CausalKnowledge",
    "RelationalKnowledge",
    "ConditionalKnowledge",
    "CurationResult",
    "OrganizationResult",
    "RetrievalResult",
    "ReasoningResult",
    "ActionResult",
    "LearningResult",
    "CORRALResult",
    "CORRALConfig",
]
