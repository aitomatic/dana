"""Base reasoning pattern for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

class BaseReasoning(ABC):
    """Base class for reasoning patterns."""
    
    def __init__(self):
        """Initialize base reasoning."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._llm_fn = None
        # Set up internal LLM-specific logger
        self.llm_logger = logging.getLogger('dxa.llm.internal')
    
    def set_llm_fn(self, llm_fn):
        """Set the LLM function to use."""
        self._llm_fn = llm_fn

    async def _log_llm_interaction(
        self,
        interaction_type: str,
        request: Dict[str, Any],
        response: Optional[Dict] = None,
        error: Optional[Exception] = None
    ):
        """Log an internal LLM interaction."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "interaction_type": interaction_type,
            "llm_type": "internal_agent",
            "reasoning_type": self.__class__.__name__,
            "request": request
        }

        if response:
            log_entry["response"] = response
        if error:
            log_entry["error"] = str(error)

        self.llm_logger.info(json.dumps(log_entry))

    async def _query_llm(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the agent's internal LLM."""
        if self._llm_fn is None:
            raise RuntimeError("LLM function not set. Call set_llm_fn first.")

        if not isinstance(request, dict) or 'prompt' not in request:
            raise ValueError("Request must be a dictionary with 'prompt' key")

        if not isinstance(request['prompt'], str):
            raise ValueError("Prompt must be a string")

        # Log the request
        await self._log_llm_interaction(
            interaction_type="request",
            request=request
        )

        try:
            response = await self._llm_fn(request)
            # Log the successful response
            await self._log_llm_interaction(
                interaction_type="response",
                request=request,
                response=response
            )
            return response
        except Exception as e:
            # Log the error
            await self._log_llm_interaction(
                interaction_type="error",
                request=request,
                error=e
            )
            self.logger.error("LLM query failed: %s", str(e))
            raise

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