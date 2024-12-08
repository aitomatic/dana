"""LLM resource implementation for DXA.

This module provides a wrapper for Large Language Model interactions,
specifically designed for OpenAI's GPT models. It handles API communication,
prompt management, and response processing.

Classes:
    LLMError: Exception class for LLM-related errors
    LLMResource: Base resource class for LLM interactions

Features:
    - Async API communication
    - System prompt management
    - Token limit handling
    - Usage tracking
    - Error handling

Example:
    llm = LLMResource(
        name="gpt4",
        config={
            "api_key": "your-api-key",
            "model": "gpt-4"
        },
        system_prompt="You are a helpful assistant."
    )
    
    response = await llm.query({
        "prompt": "Explain quantum computing",
        "temperature": 0.7
    })
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI

from dxa.core.resource.base_resource import (
    BaseResource, 
    ResourceConfig, 
    ResourceResponse, 
    ResourceError
)

class LLMError(ResourceError):
    """Error in LLM interaction."""
    pass

@dataclass
class LLMConfig(ResourceConfig):
    """LLM-specific configuration."""
    api_key: str
    model: str
    system_prompt: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class LLMResponse(ResourceResponse):
    """LLM-specific response."""
    success: bool = True
    error: Optional[str] = None
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None

class LLMResource(BaseResource):
    """LLM resource with typed config and response."""
    
    def __init__(
        self,
        name: str,
        config: LLMConfig,
        description: Optional[str] = None
    ):
        """Initialize LLM resource."""
        super().__init__(name, description, config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the LLM client."""
        try:
            self._client = AsyncOpenAI(api_key=self.config.api_key)
            self._is_available = True
            self.logger.info("LLM resource initialized successfully")
        except Exception as e:
            self._is_available = False
            self.logger.error("Failed to initialize LLM resource: %s", str(e))
            raise LLMError(f"LLM initialization failed: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up any resources used by the LLM resource."""
        await super().cleanup()
        if self._client:
            await self._client.close()
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this LLM can handle the request.
        
        This is a general-knowledge LLM that can handle:
        1. Text-based queries
        2. Requests with clear prompts
        3. Requests within its context window
        
        Args:
            request: The request to check, must contain:
                - prompt: The text prompt to process
                - max_tokens (optional): Maximum response length
        
        Returns:
            True if the request can be handled, False otherwise
        """
        # Must have a prompt
        if 'prompt' not in request or not isinstance(request['prompt'], str):
            return False
            
        # Check if prompt is empty
        if not request['prompt'].strip():
            return False
            
        # Check if within context window (if specified)
        max_tokens = request.get('max_tokens', 0)
        if max_tokens and max_tokens > 4000:  # GPT-4's limit
            return False
            
        # This is a general-knowledge LLM, so it can handle
        # any well-formed text prompt within its limits
        return True

    async def query(self, request: Dict[str, Any]) -> LLMResponse:
        """Query the LLM with typed response."""
        if not self._client:
            await self.initialize()

        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": request["prompt"]}],
                **request.get("parameters", {})
            )
            
            # pylint: disable=unexpected-keyword-arg
            return LLMResponse(
                content=response.choices[0].message.content,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                } if hasattr(response, 'usage') else None,
                model=response.model
            )
            
        except Exception as e:
            raise LLMError(f"LLM query failed: {str(e)}") from e