"""Base reasoning pattern for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

class BaseReasoning(ABC):
    """Base class for reasoning patterns."""
    
    def __init__(self):
        """Initialize base reasoning."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._llm_fn = None
    
    def set_llm_fn(self, llm_fn):
        """Set the LLM function to use."""
        self._llm_fn = llm_fn

    async def _query_llm(self, prompt: str) -> str:
        """Query the LLM with a prompt."""
        if self._llm_fn is None:
            raise RuntimeError("LLM function not set. Call set_llm_fn first.")
        return await self._llm_fn(prompt)

    @abstractmethod
    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute reasoning process."""
        pass

    @abstractmethod
    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the prompt template for this reasoning pattern."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize reasoning pattern."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 