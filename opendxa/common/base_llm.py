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

import warnings

# Add deprecation warning at top of file
warnings.warn(
    "BaseLLM is deprecated and will be removed in a future version. "
    "Use LLMResource with aisuite directly instead.",
    DeprecationWarning,
    stacklevel=2
)

from typing import Dict, Optional, List, Any, Union
import logging
import os
from dataclasses import dataclass, field
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError, AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam
)

from .exceptions import LLMError

@dataclass
class LLMConfig:
    """Configuration for LLM instances."""
    name: str
    model_name: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    additional_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, config: Optional[Dict[str, Any]] = None) -> 'LLMConfig':
        """Build LLMConfig from dictionary."""
        if not config:
            config = {}
        return cls(
            name=name,
            model_name=config.get("model", "gpt-4"),
            api_key=config.get("api_key"),
            temperature=float(config.get("temperature", 0.7)),
            max_tokens=int(config.get("max_tokens", 0)) or None,
            top_p=float(config.get("top_p", 1.0)),
            additional_params=config.get("additional_params", {})
        )

# pylint: disable=too-many-instance-attributes
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
    
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        name: str,
        config: Union[Dict[str, str], LLMConfig],
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the LLM."""
        self._config = config if isinstance(config, LLMConfig) else LLMConfig.from_dict(name, config)
        self.name = name or self._config.name
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[AsyncOpenAI] = None
        
        self.logger = logging.getLogger(f"dxa.llm.{name}")
        self.logger_extra = {
            "llm_name": self.name,
            "model": self.model_name,
            "interaction_type": 'none'
        }

    @property
    def config(self) -> LLMConfig:
        """Get the LLM configuration."""
        if not self._config:
            self._config = LLMConfig.from_dict(self.name, {})
        return self._config
    
    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        if not self.config.api_key:
            self.config.api_key = os.environ.get("DEFAULT_LLM_KEY")
        return self.config.api_key

    @property
    def model_name(self) -> str:
        """Get the model name."""
        if not self.config.model_name:
            self.config.model_name = os.environ.get("DEFAULT_LLM", "gpt-4")
        return self.config.model_name

    @property
    def temperature(self) -> float:
        """Get the temperature."""
        return self.config.temperature

    @property
    def top_p(self) -> float:
        """Get the top_p."""
        return self.config.top_p

    @property
    def max_tokens(self) -> Optional[int]:
        """Get the max_tokens."""
        return self.config.max_tokens

    @property
    def additional_params(self) -> Dict[str, Any]:
        """Get the additional_params."""
        return self.config.additional_params

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._client:
            try:
                self._client = AsyncOpenAI(api_key=self.api_key)
                self.logger.info("LLM client initialized successfully", extra=self.logger_extra)
            except Exception as e:
                self.logger.error("Failed to initialize LLM client: %s", str(e), extra=self.logger_extra)
                raise LLMError(f"LLM initialization failed: {str(e)}") from e

    async def query(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ChatCompletion:
        """Send a raw query to the LLM and log the interaction."""
        if not self._client:
            await self.initialize()

        # Merge instance config with any request-specific kwargs
        request_config = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            **kwargs
        }
        if self.max_tokens:
            request_config["max_tokens"] = self.max_tokens

        # Log the request
        self.logger.info("LLM Request", extra={
            **self.logger_extra,
            "messages": messages,
            "parameters": request_config,
            "interaction_type": "request"
        })

        # flake8: noqa: E501
        messages_typed = [
            ChatCompletionSystemMessageParam(content=msg["content"], role="system") if msg["role"] == "system" else
            ChatCompletionUserMessageParam(content=msg["content"], role="user") if msg["role"] == "user" else
            ChatCompletionAssistantMessageParam(content=msg["content"], role="assistant") if msg["role"] == "assistant" else
            ChatCompletionUserMessageParam(content=msg["content"], role="user")
            for msg in messages
        ]
        try:
            assert isinstance(self._client, AsyncOpenAI)
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages_typed,
                **request_config
            )

            # Safely get token usage
            token_usage = None
            if response.usage:
                token_usage = response.usage.total_tokens

            # Log the response
            self.logger.info("LLM Response", extra={
                **self.logger_extra,
                "response": response.model_dump() if hasattr(response, 'model_dump') else str(response),
                "interaction_type": "response",
                "tokens": token_usage
            })

            return response

        except (APIError, APIConnectionError, RateLimitError, APITimeoutError) as e:
            # Log the error
            self.logger.error("LLM Error", extra={
                **self.logger_extra,
                "error": str(e),
                "interaction_type": "error"
            })
            raise LLMError(f"LLM query failed: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up any resources used by the LLM."""
        if self._client:
            await self._client.close()
            self._client = None
