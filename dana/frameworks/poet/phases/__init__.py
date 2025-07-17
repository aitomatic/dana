"""POET Phases - P→O→E→T Implementation

This module provides the four core phases of the POET framework:
- Perceive: Input validation and preprocessing
- Operate: Enhanced function execution with retry logic
- Enforce: Output validation and quality assurance
- Train: Learning and feedback collection
"""

from .enforce import EnforcePhase
from .operate import OperatePhase
from .perceive import PerceivePhase
from .train import TrainPhase

# Convenience functions that create phase instances
def perceive(config):
    """Create a PerceivePhase instance."""
    return PerceivePhase(config)

def operate(config):
    """Create an OperatePhase instance."""
    return OperatePhase(config)

def enforce(config):
    """Create an EnforcePhase instance."""
    return EnforcePhase(config)

def train(config):
    """Create a TrainPhase instance."""
    return TrainPhase(config)

__all__ = [
    "PerceivePhase",
    "OperatePhase", 
    "EnforcePhase",
    "TrainPhase",
    "perceive",
    "operate",
    "enforce",
    "train",
]