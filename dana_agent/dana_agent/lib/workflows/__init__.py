"""
Example workflow implementations for the Dana framework.

This module provides example workflows that demonstrate how to create
and use workflows with agents.
"""

from .web_research import (
    ExtractAnswerWorkflow,
    ExtractFactWorkflow,
    FactFindingWorkflow,
    FetchResultWorkflow,
    FormatWorkflow,
    GoogleLookupWorkflow,
    ResearchSynthesisWorkflow,
    SearchWorkflow,
    SingleSourceDeepDiveWorkflow,
    StructuredDataNavigationWorkflow,
)


__all__ = [
    "SearchWorkflow",
    "FetchResultWorkflow",
    "ExtractAnswerWorkflow",
    "GoogleLookupWorkflow",
    "ExtractFactWorkflow",
    "FormatWorkflow",
    "FactFindingWorkflow",
    "SingleSourceDeepDiveWorkflow",
    "ResearchSynthesisWorkflow",
    "StructuredDataNavigationWorkflow",
]
