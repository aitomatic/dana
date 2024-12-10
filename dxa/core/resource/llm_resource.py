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

from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from openai import AsyncOpenAI

from dxa.core.resource.base_resource import (
    BaseResource, 
    ResourceResponse, 
    ResourceError,
    ResourceConfig
)
from dxa.core.config import LLMConfig

class LLMError(ResourceError):
    """Error in LLM interaction."""
    pass

@dataclass
class LLMResponse(ResourceResponse):
    """LLM-specific response."""
    success: bool = True
    error: Optional[str] = None
    content: str = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None

class LLMResource(BaseResource):
    """LLM resource with typed config and response."""
    
    def __init__(
        self,
        name: str,
        config: Union[Dict[str, Any], LLMConfig],
        description: Optional[str] = None
    ):
        """Initialize LLM resource."""
        if isinstance(config, dict):
            config = LLMConfig(**config)
        
        resource_config = ResourceConfig(
            name=name,
            description=description,
        )

        if isinstance(config, LLMConfig):
            resource_config.llm_config = config

        super().__init__(name, description, resource_config)
        self._client = None

    async def initialize(self) -> None:
        """Initialize the LLM client."""
        try:
            self._client = AsyncOpenAI(api_key=self.config.llm_config.api_key)
            self._is_available = True
            self.logger.info("LLM resource initialized successfully")
        except Exception as e:
            self._is_available = False
            self.logger.error("Failed to initialize LLM resource: %s", str(e))
            raise LLMError(f"LLM initialization failed: {str(e)}") from e

    @property  
    def llm_config(self) -> LLMConfig:
        """Get the LLM config."""
        return self.config.llm_config
    
    @llm_config.setter
    def set_llm_config(self, llm_config: LLMConfig) -> None:
        """Set the LLM config."""
        self.config.llm_config = llm_config
    
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
            messages = []
            # Add system prompt if configured
            if self.llm_config.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.llm_config.system_prompt
                })
            # Add user message
            messages.append({
                "role": "user", 
                "content": request["prompt"]
            })

            response = await self._client.chat.completions.create(
                model=self.llm_config.model_name,
                messages=messages,
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