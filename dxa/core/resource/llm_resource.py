"""LLM resource implementation."""

from typing import Dict, Any, Optional
import asyncio
from .base_resource import BaseResource
from ...common.base_llm import BaseLLM, LLMConfig

class LLMResource(BaseResource):
    """LLM resource implementation using BaseLLM."""
    
    def __init__(self, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource."""
        if name is None:
            name = "default_llm"

        super().__init__(name)
        self.config = LLMConfig.from_dict(name, config)
        self._llm = BaseLLM(name=self.name, config=self.config)

    async def initialize(self) -> None:
        """Initialize the LLM."""
        await self._llm.initialize()

    def do_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Do synchronous query to LLM (meaning wait for response)."""
        return asyncio.run(self.query(request))

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to LLM.
        Args:
            request: Dictionary with "prompt" key. Optional "system_prompt" key will override the LLM's system prompt.
        Returns:
            Dictionary with "content", "model", and "usage" keys.
        """
        messages = []
        if "system_prompt" in request:
            messages.append({"role": "system", "content": request["system_prompt"]})
        elif self._llm.system_prompt:
            messages.append({"role": "system", "content": self._llm.system_prompt})

        if "prompt" in request:
            messages.append({"role": "user", "content": request["prompt"]})
        else:
            raise ValueError("'Prompt is required")
        
        response = await self._llm.query(messages)
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": response.usage.model_dump() if response.usage else None
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._llm.cleanup()

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request