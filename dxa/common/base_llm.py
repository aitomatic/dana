"""Base LLM (Large Language Model) implementation for the DXA system.

This module provides the foundational LLM interface used throughout the DXA system.
It handles common LLM operations including:
- Asynchronous initialization and cleanup
- Retry logic for failed requests
- Standardized error handling
- Configuration management

The BaseLLM class can be extended to support different LLM providers while
maintaining consistent behavior across the system.
"""

from typing import Dict, Any, Optional, List
import asyncio
import logging
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
import openai

from .exceptions import LLMError

class BaseLLM:
    """Base class for LLM interactions."""
    
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
        """Query the LLM with retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments to pass to the chat completion
        
        Returns:
            ChatCompletion response from the API
        
        Raises:
            LLMError: If the query fails after all retries
        """
        if not self._client:
            await self.initialize()

        for attempt in range(self.max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                return response
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
