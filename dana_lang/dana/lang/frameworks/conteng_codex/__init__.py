"""
Codex Minimal Context Engineering (CE) Framework

This package provides a minimal, runnable implementation of Context Engineering
focused on clear schemas and a small, working pipeline:
- ContextTemplate/Instance/Spec with token budgets and selectors
- KnowledgeAsset + DomainRegistry (in‑memory) for templates and assets
- ContextArchitect that assembles contexts deterministically with caching
- A tiny example domain pack (simple_finance) to demonstrate usage

The goal is to be small, consistent, and usable in Phase A evaluations.
"""

from .templates import (
    ContextTemplate,
    ContextInstance,
    ContextSpec,
    TokenBudget,
    KnowledgeSelector,
    ContextMerger,
)
from .registry import (
    KnowledgeAsset,
    DomainRegistry,
)
from .architect import ContextArchitect

__all__ = [
    "ContextTemplate",
    "ContextInstance",
    "ContextSpec",
    "TokenBudget",
    "KnowledgeSelector",
    "ContextMerger",
    "KnowledgeAsset",
    "DomainRegistry",
    "ContextArchitect",
]
