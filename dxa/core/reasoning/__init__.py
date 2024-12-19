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

from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.reasoning.direct_reasoning import DirectReasoning
from dxa.core.reasoning.cot_reasoning import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda_reasoning import OODAReasoning
from dxa.core.reasoning.dana_reasoning import DANAReasoning

__all__ = [
    'BaseReasoning',
    'DirectReasoning',
    'ChainOfThoughtReasoning',
    'OODAReasoning',
    'DANAReasoning'
] 