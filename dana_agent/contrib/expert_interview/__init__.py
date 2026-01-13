"""
Expert Interview Application

A simple expert interview application built on Dana's conversation and analysis resources.

Components:
- Resources: ExpertInsightAnalyzer, KnowledgeGapDetector
- Workflows: ExpertInterviewWorkflow
- CLI: Simple command-line interview tool
"""

from .resources import ExpertInsightAnalyzer, KnowledgeGapDetector
from .workflows import ExpertInterviewWorkflow


__version__ = "0.1.0"

__all__ = [
    "ExpertInsightAnalyzer",
    "KnowledgeGapDetector",
    "ExpertInterviewWorkflow",
]
