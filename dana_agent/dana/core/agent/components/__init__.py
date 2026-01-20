"""
Agent components for composition-based STAR agent architecture.

This package provides components that can be composed to create STAR agents
with different capabilities:

- Communicator: LLM integration and agent communication
- State: State management and timeline functionality
- Learner: STAR learning phases and reflection
- PythonSandbox: Safe Python execution environment for RLM pattern

Legacy components (deprecated - use DefaultRuntime instead):
- LegacyPromptEngineer: XML-based prompt file handling (alias: PromptEngineer)
- LegacyToolCaller: Tool call execution (alias: ToolCaller)
- LegacyCodecToolCaller: Codec-based tool calling (alias: CodecToolCaller)
"""

from .communicator import Communicator
from .learner import Learner, LearnerProtocol
from .observer import NullObserver, ObserverProtocol
from .prompt_engineer import LegacyPromptEngineer, PromptEngineer
from .python_sandbox import PythonSandbox
from .state import State
from .tool_caller import CodecToolCaller, LegacyCodecToolCaller, LegacyToolCaller, ToolCaller


__all__ = [
    "Communicator",
    "Learner",
    "LearnerProtocol",
    "NullObserver",
    "ObserverProtocol",
    "PythonSandbox",
    "State",
    # Legacy components (deprecated)
    "LegacyPromptEngineer",
    "LegacyToolCaller",
    "LegacyCodecToolCaller",
    # Backward-compatible aliases
    "PromptEngineer",
    "ToolCaller",
    "CodecToolCaller",
]
