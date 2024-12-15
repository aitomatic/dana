"""Reasoning patterns for DXA.

This module provides different reasoning strategies with increasing complexity:

1. DirectReasoning: 
   - Simple direct execution without complex reasoning
   - Best for straightforward tasks with clear steps
   - Lowest overhead, fastest execution

2. ChainOfThoughtReasoning:
   - Linear step-by-step reasoning with explicit thought process
   - Best for problems requiring detailed explanation
   - Includes understanding, analysis, solution, and verification

3. OODAReasoning:
   - Observe-Orient-Decide-Act loop for dynamic situations
   - Best for problems requiring continuous adaptation
   - Handles changing conditions and requirements

4. DANAReasoning:
   - Domain-Aware Neurosymbolic Agent combining neural and symbolic approaches
   - Best for problems requiring precise computation with domain knowledge
   - Bridges LLM reasoning with symbolic execution

Each pattern is designed for specific use cases and complexity levels.
Choose based on your task requirements and need for reasoning complexity.
"""

from dxa.core.reasoning.base_reasoning import (
    BaseReasoning,
    ReasoningStatus,
    ReasoningLevel,
    ReasoningResult,
    ReasoningContext,
    ReasoningConfig,
    ObjectiveState
)
from dxa.core.reasoning.direct_reasoning import DirectReasoning
from dxa.core.reasoning.cot_reasoning import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda_reasoning import OODAReasoning
from dxa.core.reasoning.dana_reasoning import DANAReasoning

__all__ = [
    'BaseReasoning',
    'ReasoningStatus',
    'ReasoningLevel',
    'ReasoningResult',
    'ReasoningContext',
    'ReasoningConfig',
    'ObjectiveState',
    'DirectReasoning',
    'ChainOfThoughtReasoning',
    'OODAReasoning',
    'DANAReasoning'
] 