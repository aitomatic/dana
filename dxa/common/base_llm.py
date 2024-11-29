"""Base LLM (Large Language Model) implementation.

This module provides a basic LLM interface that handles raw interactions with 
language models. It provides straightforward query functionality without any
domain-specific prompt management or context handling.

Example:
    ```python
    llm = BaseLLM(
        name="basic_llm",
        config={
            "model": "gpt-4",
            "api_key": "your-key"
        }
    )
    
    response = await llm.query([
        {"role": "user", "content": "Hello!"}
    ])
    ```
"""

from typing import Dict, Optional, List
import logging
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError, AsyncOpenAI
from openai.types.chat import ChatCompletion

from .exceptions import LLMError

class BaseLLM:
    """Base class for raw LLM interactions.
    
    This class provides direct access to language model capabilities without
    any additional prompt management or context handling. It's designed to be
    a simple wrapper around the OpenAI API.
    
    Attributes:
        name: Name identifier for this LLM instance
        api_key: OpenAI API key
        model: Name of the model to use
        config: Additional configuration parameters
        
    Args:
        name: Name for this LLM instance
        config: Configuration dictionary containing api_key and other settings
        system_prompt: Optional system prompt to use for all queries
        max_retries: Maximum number of retries for failed requests
        retry_delay: Delay between retries in seconds
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, str],
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the LLM.
        
        Args:
            name: Name identifier for this LLM instance
            config: Configuration dictionary containing api_key and other settings
            system_prompt: Optional system prompt to use for all queries
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.name = name
        self.api_key = config.pop('api_key', '')
        self.model = config.pop('model', 'gpt-4')
        self.config = config
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger(f"dxa.llm.{name}")

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._client:
            try:
                self._client = AsyncOpenAI(api_key=self.api_key)
                self.logger.info("LLM client initialized successfully")
            except Exception as e:
                self.logger.error("Failed to initialize LLM client: %s", str(e))
                raise LLMError(f"LLM initialization failed: {str(e)}") from e

    async def query(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ChatCompletion:
        """Send a raw query to the LLM and log the interaction."""
        if not self._client:
            await self.initialize()

        # Log the request
        self.logger.info("LLM Request", extra={
            "llm_name": self.name,
            "model": self.model,
            "messages": messages,
            "parameters": kwargs,
            "interaction_type": "request"
        })

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )

            # Safely get token usage
            token_usage = None
            if response.usage:
                token_usage = response.usage.total_tokens

            # Log the response
            self.logger.info("LLM Response", extra={
                "llm_name": self.name,
                "model": self.model,
                "response": response.model_dump() if hasattr(response, 'model_dump') else str(response),
                "interaction_type": "response",
                "tokens": token_usage
            })

            return response

        except (APIError, APIConnectionError, RateLimitError, APITimeoutError) as e:
            # Log the error
            self.logger.error("LLM Error", extra={
                "llm_name": self.name,
                "model": self.model,
                "error": str(e),
                "interaction_type": "error"
            })
            raise LLMError(f"LLM query failed: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up any resources used by the LLM."""
        if self._client:
            await self._client.close()
            self._client = None
