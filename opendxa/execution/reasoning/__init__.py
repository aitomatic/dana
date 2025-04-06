"""Reasoning module for DXA.

This module provides the core reasoning capabilities for DXA agents.
See README.md for detailed documentation of available reasoning patterns.

Exports:
    BaseReasoning: Abstract base class for reasoning implementations
    DirectReasoning: Simple direct execution
    ChainOfThoughtReasoning: Step-by-step reasoning
    OODAReasoning: Dynamic adaptation loop
    DANAReasoning: Domain-aware computation

Supporting Types:
    ReasoningStatus: Status enums for reasoning steps
    ReasoningLevel: Complexity levels for reasoning
    ReasoningResult: Output from reasoning process
    ReasoningContext: State and resource management
    ReasoningConfig: Configuration options
    ObjectiveState: Objective tracking
"""

from .reasoning import Reasoning
from .reasoning_factory import ReasoningFactory
from .reasoning_strategy import ReasoningStrategy
from .reasoning_executor import ReasoningExecutor

__all__ = [
    'Reasoning',
    'ReasoningFactory',
    'ReasoningStrategy',
    'ReasoningExecutor',
] 