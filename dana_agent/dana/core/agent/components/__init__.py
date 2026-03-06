"""
Agent components for composition-based STAR agent architecture.

This package provides components that can be composed to create STAR agents
with different capabilities:

- Communicator: LLM integration and agent communication
- State: State management and timeline functionality
- Learner: STAR learning phases and reflection
- PythonSandbox: Safe Python execution environment for RLM pattern
"""

from .communicator import Communicator
from .learner import Learner, LearnerProtocol
from .observer import NullObserver, ObserverProtocol
from .python_sandbox import PythonSandbox
from .state import State


__all__ = [
    "Communicator",
    "Learner",
    "LearnerProtocol",
    "NullObserver",
    "ObserverProtocol",
    "PythonSandbox",
    "State",
]
