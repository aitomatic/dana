"""Execution strategy implementations."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

class ExecutionStrategy(ABC):
    """Base class for execution strategies."""
    
    @abstractmethod
    async def execute(self, reasoning: Any, objective: Any) -> AsyncIterator[Any]:
        """Execute using this strategy."""
        raise NotImplementedError

class SingleShotStrategy(ExecutionStrategy):
    """One-and-done execution."""
    
    async def execute(self, reasoning, objective):
        yield await reasoning.reason_about_step(objective.to_step())

class IterativeStrategy(ExecutionStrategy):
    """Repeated attempt execution."""
 