"""Reasoning pattern implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict

class ReasoningPattern(ABC):
    """Base class for reasoning patterns."""
    
    @abstractmethod
    async def reason_about_step(self, step: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Apply reasoning pattern to a step."""
        raise NotImplementedError

class DirectReasoning(ReasoningPattern):
    """Single-step direct reasoning."""
    
    async def reason_about_step(self, step, context):
        return await context.llm.query(self._create_prompt(step))

class ChainOfThoughtReasoning(ReasoningPattern):
    """Step-by-step deductive reasoning."""
    
    async def reason_about_step(self, step, context):
        # Implementation 