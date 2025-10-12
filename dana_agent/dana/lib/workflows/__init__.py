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
    SingleSourceDeepDiveWorkflow,
    StructuredDataNavigationWorkflow,
)


__all__ = [
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
