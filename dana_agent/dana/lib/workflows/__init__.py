"""
Example workflow implementations for the Dana framework.

This module provides example workflows that demonstrate how to create
and use workflows with agents.
"""

from .conversation import (
    SummarizeConversationWorkflow,
)
from .web_research import (
    FactFindingWorkflow,
    GoogleLookupWorkflow,
    ResearchSynthesisWorkflow,
    StructuredDataNavigationWorkflow,
)


__all__ = [
    # Conversation workflows
    "SummarizeConversationWorkflow",
    # Web research workflows
    "GoogleLookupWorkflow",
    "FactFindingWorkflow",
    "ResearchSynthesisWorkflow",
    "StructuredDataNavigationWorkflow",
]
