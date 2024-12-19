"""
Core interfaces defining how Reasoning processes individual steps
and generates signals.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..types import Step, Signal


class BaseReasoning(ABC):
    """
    Reasoning is responsible for:
    1. Reasoning about individual steps
    2. Generating signals about discoveries
    3. Determining step completion/failure
    """

    @abstractmethod
    async def reason_about(
        self,
        step: Step,
        context: Dict[str, Any],
        resources: Dict[str, Any]
    ) -> List[Signal]:
        """
        Apply reasoning pattern to a step.
        
        Args:
            step: The step to reason about
            context: Current execution context
            resources: Available resources
            
        Returns:
            List[Signal]: Signals about discoveries, completion, etc.
        """
        pass

    @abstractmethod
    async def validate(
        self,
        step: Step,
        result: Dict[str, Any]
    ) -> bool:
        """
        Validate the reasoning result for a step.
        
        Args:
            step: The step that was executed
            result: The result to validate
            
        Returns:
            bool: True if result is valid, False otherwise
        """
        pass