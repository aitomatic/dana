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

from typing import Dict, Any, Optional, List
import asyncio
import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
import openai

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
        config: Dict[str, Any],
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
        self.api_key = config.pop('api_key')
        self.model = config.pop('model', 'gpt-4')
        self.config = config
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger(self.__class__.__name__)

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
        """Send a raw query to the LLM.
        
        Provides direct access to the OpenAI chat completion API without any
        additional processing or prompt management.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments to pass to the chat completion
            
        Returns:
            Raw ChatCompletion response from the API
            
        Example:
            ```python
            response = await llm.query([
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello!"}
            ])
            print(response.choices[0].message.content)
            ```
        """
        if not self._client:
            await self.initialize()

        for attempt in range(self.max_retries):
            try:
                return await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
            except (openai.APIError, openai.APIConnectionError, openai.RateLimitError, openai.APITimeoutError) as e:
                self.logger.warning(
                    "LLM query attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries,
                    str(e)
                )
                if attempt + 1 == self.max_retries:
                    raise LLMError(f"LLM query failed after {self.max_retries} attempts: {str(e)}") from e
                await asyncio.sleep(self.retry_delay)

    async def cleanup(self) -> None:
        """Clean up any resources used by the LLM."""
        if self._client:
            await self._client.close()
            self._client = None
