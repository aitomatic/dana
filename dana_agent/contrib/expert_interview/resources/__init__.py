"""
Expert Interview Resources

Domain-agnostic resources for expert knowledge capture:
- ExpertInsightAnalyzer: Extract insights with quote preservation
- KnowledgeGapDetector: Identify gaps between sources
"""

from .expert_insights import ExpertInsightAnalyzer
from .knowledge_gaps import KnowledgeGapDetector


__all__ = [
    "ExpertInsightAnalyzer",
    "KnowledgeGapDetector",
]
