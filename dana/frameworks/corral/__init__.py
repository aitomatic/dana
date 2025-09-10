"""CORRAL Framework - Complete Knowledge Lifecycle for Dana Agents.

The CORRAL framework implements a complete knowledge lifecycle:
Curate → Organize → Retrieve → Reason → Act → Learn

This enables Dana agents to build, maintain, and continuously improve
their knowledge through direct experience and outcome feedback.

The framework uses the composition pattern:
- CORRALEngineer: Core service class (like ctxeng)
"""

from .config import CORRALConfig
from .engineer import CORRALEngineer
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
    # Core service class
    "CORRALEngineer",
    # Knowledge types
    "Knowledge",
    "KnowledgeCategory",
    "DeclarativeKnowledge",
    "ProceduralKnowledge",
    "CausalKnowledge",
    "RelationalKnowledge",
    "ConditionalKnowledge",
    # Result types
    "CurationResult",
    "OrganizationResult",
    "RetrievalResult",
    "ReasoningResult",
    "ActionResult",
    "LearningResult",
    "CORRALResult",
    # Configuration
    "CORRALConfig",
]
