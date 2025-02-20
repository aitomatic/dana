"""LLM resource implementation."""

from typing import Dict, Any, Optional
import asyncio
import aisuite as ai
from openai import APIConnectionError, RateLimitError
from ...common.exceptions import LLMError
from .base_resource import BaseResource


class LLMConfig:
    """Configuration for LLM instances using AISuite."""
    
    def __init__(
        self,
        model: str = "openai:gpt-4",
        providers: Optional[Dict[str, Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any
    ) -> None:
        """Initialize LLM configuration.
        
        Args:
            model: Model identifier in format "provider:model" (e.g. "openai:gpt-4")
            providers: Dictionary of provider configurations
            temperature: Float between 0 and 1
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries in seconds
            **kwargs: Additional configuration parameters
        """
        self.model = model
        self.providers = providers or {}
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.additional_params = kwargs

    @classmethod
    def from_dict(cls, config: Optional[Dict[str, Any]] = None) -> 'LLMConfig':
        """Build LLMConfig from dictionary."""
        if not config:
            return cls()
            
        # Extract known parameters
        known_params = {
            'model', 'providers', 'temperature', 'max_tokens',
            'top_p', 'max_retries', 'retry_delay'
        }
        config_params = {k: v for k, v in config.items() if k in known_params}
        
        # Pass remaining parameters as additional_params
        additional_params = {k: v for k, v in config.items() if k not in known_params}
        
        return cls(**config_params, **additional_params)


class LLMResource(BaseResource):
    """LLM resource implementation using AISuite."""
    
    def __init__(self, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource.
        
        Args:
            name: Resource name
            config: Configuration dictionary containing:
                - model: Model identifier in format "provider:model" (e.g. "openai:gpt-4")
                - providers: Dictionary of provider configurations
                - temperature: Float between 0 and 1
                - api_key: Optional API key (will use environment variables if not provided)
                - additional provider-specific parameters
        """

        if name is None:
            name = "default_llm"

        super().__init__(name)
        self.config = config or {}
        self.model = self.config.get("model", "openai:gpt-4")
        self.provider_configs = self.config.get("providers", {})
        self._client: Optional[ai.Client] = None
        self.max_retries = int(self.config.get("max_retries", 3))
        self.retry_delay = float(self.config.get("retry_delay", 1.0))

    async def initialize(self) -> None:
        """Initialize the AISuite client."""
        if not self._client:
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}
            
            self._client = ai.Client(provider_configs=self.provider_configs)
            self.logger.info("LLM client initialized successfully for model: %s", self.model)

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to LLM.
        
        Args:
            request: Dictionary with:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - additional parameters
        
        Returns:
            Dictionary with "content", "model", and "usage" keys.
        """
        if not self._client:
            await self.initialize()

        messages = []
        if "system_prompt" in request:
            messages.append({"role": "system", "content": request["system_prompt"]})

        if "prompt" in request:
            messages.append({"role": "user", "content": request["prompt"]})
        else:
            raise ValueError("'Prompt' is required")

        request_params = {
            "temperature": float(self.config.get("temperature", 0.7)),
            "top_p": float(self.config.get("top_p", 1.0)),
            "max_tokens": self.config.get("max_tokens"),
            "frequency_penalty": self.config.get("frequency_penalty"),
            "presence_penalty": self.config.get("presence_penalty"),
        }
        
        # Merge with request-specific params
        request_params.update(request.get("parameters", {}))
        
        # Filter out None values
        request_params = {k: v for k, v in request_params.items() if v is not None}

        for attempt in range(self.max_retries + 1):
            try:
                assert self._client is not None
                # Let aisuite handle the provider-specific response processing
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **request_params
                )

                # Use aisuite's standardized response format
                reasoning = None
                if hasattr(response, 'reasoning_content'):
                    reasoning = response.reasoning_content
                elif hasattr(response, 'choices') and hasattr(response.choices[0].message, 'reasoning_content'):
                    reasoning = response.choices[0].message.reasoning_content

                return {
                    "content": response.choices[0].message.content 
                    if hasattr(response, 'choices') else response.content,
                    "model": self.model,  # Use our model string since it's guaranteed to exist
                    "usage": getattr(response, 'usage', None),
                    # Include any thinking content if present
                    "reasoning": reasoning
                }

            except (APIConnectionError, RateLimitError) as e:
                if attempt >= self.max_retries:
                    raise e
                delay = self.retry_delay * (2 ** attempt)
                self.logger.warning("Retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, self.max_retries)
                await asyncio.sleep(delay)
            except ValueError as e:
                # Handle configuration/model format errors
                raise e
            except AttributeError as e:
                # Handle response structure mismatches
                self.logger.error("Unexpected response structure from provider: %s", str(e))
                raise LLMError(f"Unexpected response structure: {str(e)}") from e
        
        raise LLMError("Max retries exceeded")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request