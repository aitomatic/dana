"""Workflows for SmartResearchAgent."""

from .parallel_gathering import ParallelGatheringWorkflow
from .research_strategy import ResearchStrategyWorkflow
from .synthesis import SynthesisWorkflow

__all__ = [
    "ResearchStrategyWorkflow",
    "ParallelGatheringWorkflow",
    "SynthesisWorkflow",
]
