"""
Agent components for composition-based STAR agent architecture.

This package provides components that can be composed to create STAR agents
with different capabilities:

- PromptEngineer: Docstring parsing and system prompt generation
- Communicator: LLM integration and agent communication
- State: State management and timeline functionality
- Learner: STAR learning phases and reflection
- ToolCaller: Tool call execution and orchestration
"""

from .communicator import Communicator
from .learner import Learner
from .prompt_engineer import PromptEngineer
from .state import State
from .tool_caller import ToolCaller


__all__ = [
    "PromptEngineer",
    "Communicator",
    "State",
    "Learner",
    "ToolCaller",
]
