"""
Core interfaces defining how Reasoning processes individual steps
and generates signals.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..types import Signal
from ..planning import Step
from ..resource.llm_resource import LLMResource


class BaseReasoner(ABC):
    """
    Reasoning is responsible for:
    1. Reasoning about individual steps using agent's LLM
    2. Generating signals about discoveries
    3. Determining step completion/failure
    """

    @abstractmethod
    async def reason_about(
        self,
        step: Step,
        context: Dict[str, Any],
        agent_llm: LLMResource,
        resources: Dict[str, Any]
    ) -> List[Signal]:
        """
        Apply reasoning pattern to a step.
        
        Args:
            step: The step to reason about
            context: Current execution context
            agent_llm: Primary LLM for agent operations
            resources: Additional available resources
            
        Returns:
            List[Signal]: Signals about discoveries, completion, etc.
        """
        pass

    @abstractmethod
    def validate(
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