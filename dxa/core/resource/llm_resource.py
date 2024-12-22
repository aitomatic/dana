"""LLM resource implementation."""

from typing import Dict, Any, Optional
from .base_resource import BaseResource
from ...common.base_llm import BaseLLM, LLMConfig
from ...common.exceptions import ConfigurationError

class LLMResource(BaseResource):
    """LLM resource implementation using BaseLLM."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource."""
        super().__init__(name)
        self.config = LLMConfig.from_dict(name, config)
        if not self.config.api_key:
            raise ConfigurationError("API key required")
        self._llm = BaseLLM(name=self.name, config=self.config)

    async def initialize(self) -> None:
        """Initialize the LLM."""
        await self._llm.initialize()

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to LLM."""
        messages = []
        if self._llm.system_prompt:
            messages.append({"role": "system", "content": self._llm.system_prompt})
        messages.append({"role": "user", "content": request["prompt"]})
        
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