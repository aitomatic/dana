"""LLM resource implementation."""

from typing import Dict, Any, Optional
from .base_resource import BaseResource
from ...common.base_llm import BaseLLM, LLMConfig
from ...common.utils.config import load_agent_config
from ...common.exceptions import ConfigurationError

class LLMResource(BaseResource):
    """LLM resource implementation using BaseLLM."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource."""
        super().__init__(name)
        
        # Load config with environment variables
        base_config = load_agent_config("llm")
        
        # Override with provided config if any
        if config:
            base_config.update(config)
            
        self.config = LLMConfig(
            name=name,
            model_name=base_config.get("model", "gpt-4"),
            api_key=base_config.get("api_key"),
            temperature=float(base_config.get("temperature", 0.7)),
            max_tokens=int(base_config.get("max_tokens", 0)) or None,
            top_p=float(base_config.get("top_p", 1.0)),
            additional_params=base_config.get("additional_params", {})
        )
        self._llm: Optional[BaseLLM] = None

    async def initialize(self) -> None:
        """Initialize the LLM."""
        if not self.config.api_key:
            raise ConfigurationError("API key required for LLM initialization")
        
        llm_config = {
            "api_key": self.config.api_key,
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p
        }
        if self.config.max_tokens:
            llm_config["max_tokens"] = self.config.max_tokens
            
        self._llm = BaseLLM(self.config.name, llm_config)
        await self._llm.initialize()

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to LLM."""
        if not self._llm:
            await self.initialize()
            
        messages = [{"role": "user", "content": request["prompt"]}]
        response = await self._llm.query(messages)
        
        return {
            "success": True,
            "content": response.choices[0].message.content
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._llm:
            await self._llm.cleanup()

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request