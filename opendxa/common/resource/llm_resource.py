"""LLM resource implementation."""

import asyncio
import os
from typing import Any, Dict, Optional, Union, Callable

import aisuite as ai
from openai import APIConnectionError, RateLimitError
from ...common.exceptions import LLMError
from .base_resource import BaseResource

class LLMResource(BaseResource):
    """LLM resource implementation using AISuite."""

    _DEFAULT_MODEL = "deepseek:deepseek-chat"

    def _get_default_model(self) -> str:
        """Get the default model by checking the environment variable."""
        if "OPENDXA_DEFAULT_MODEL" in os.environ:
            return os.environ["OPENDXA_DEFAULT_MODEL"]
        elif "DEEPSEEK_API_KEY" in os.environ:
            return "deepseek:deepseek-chat"
        elif "ANTHROPIC_API_KEY" in os.environ:
            return "anthropic:claude-3-5-sonnet-20241022"
        elif "OPENAI_API_KEY" in os.environ:
            return "openai:gpt-4o"

        return self._DEFAULT_MODEL

    def __init__(self, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM resource.

        Args:
            name: Resource name.
            config: Configuration dictionary containing:
                - model: Model identifier in format "provider:model" (e.g. "openai:gpt-4").
                - providers: Dictionary of provider configurations.
                - temperature: Float between 0 and 1, controlling the randomness of the LLM's output.
                - api_key: Optional API key (will use environment variables if not provided).
                - mock_llm_call: Optional flag or function for mocking LLM responses.
                  If 'mock_llm_call' is a callable, it will be called with the request
                  and its return value will be used as the response.
                  If 'mock_llm_call' is set but not callable, the '_mock_llm_query' method
                  will be used, which returns a basic response echoing the prompt.
                - max_retries: Maximum number of retry attempts for LLM queries.
                - retry_delay: Delay in seconds between retry attempts.
                - additional provider-specific parameters.
        """

        if name is None:
            name = "default_llm_resource"

        super().__init__(name)
        self.config = config or {}
        self.model = self.config.get("model", self._get_default_model())
        self.provider_configs = self.config.get("providers", {})
        self._client: Optional[ai.Client] = None
        self.max_retries = int(self.config.get("max_retries", 3))
        self.retry_delay = float(self.config.get("retry_delay", 1.0))
        self._mock_llm_call = self.config.get("mock_llm_call", None)
        # self._async_client = AsyncClient()
        
        # Add a file handler to the existing logger if needed
        import logging
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.logger.handlers):
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Add file handler with the same format as before
            file_handler = logging.FileHandler("logs/llm_conversation.log")
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.logger.addHandler(file_handler)

    async def initialize(self) -> None:
        """Initialize the AISuite client."""
        if not self._client:
            # Handle backward compatibility for top-level api_key
            if "api_key" in self.config and "openai" not in self.provider_configs:
                self.provider_configs["openai"] = {"api_key": self.config["api_key"]}

            self._client = ai.Client(provider_configs=self.provider_configs)
            self.logger.info("LLM client initialized successfully for model: %s", self.model)

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to LLM or use mock if set.

        Args:
            request: Dictionary with:
                - prompt: The user message
                - system_prompt: Optional system prompt
                - tools: Optional list of resources to use as tools
                - max_retries: Optional integer to override the default max_retries value.
                - additional parameters

        Returns:
            Dictionary with "content", "model", "usage", and "requested_tools" keys.
        """
        # Check for mock flag or function
        if callable(self._mock_llm_call):
            return await self._mock_llm_call(request)
        elif self._mock_llm_call:
            return await self._mock_llm_query(request)

        if not self._client:
            await self.initialize()

        messages = []
        if "system_prompt" in request:
            messages.append({"role": "system", "content": request["system_prompt"]})

        if "prompt" in request:
            messages.append({"role": "user", "content": request["prompt"]})
        else:
            raise ValueError("'Prompt' is required")

        # Log the prompt being sent to the LLM
        self.logger.info(f"PROMPT TO {self.model}:\n{'-' * 80}\n{messages}\n{'-' * 80}")
        
        request_params = {
            "temperature": float(self.config.get("temperature", 0.7)),
            "top_p": float(self.config.get("top_p", 1.0)),
            "max_tokens": self.config.get("max_tokens"),
            "frequency_penalty": self.config.get("frequency_penalty"),
            "presence_penalty": self.config.get("presence_penalty"),
        }

        # Add tools if provided in the request
        if "tools" in request and request["tools"]:
            request_params["tools"] = request["tools"]

        # Merge with request-specific params
        request_params.update(request.get("parameters", {}))

        # Filter out None values
        request_params = {k: v for k, v in request_params.items() if v is not None}

        # Use max_retries from request if provided, otherwise use default
        max_retries = request.get('max_retries', self.max_retries)

        for attempt in range(max_retries + 1):
            try:
                assert self._client is not None
                # Let aisuite handle the provider-specific response processing
                response = self._client.chat.completions.create(model=self.model, messages=messages, **request_params)

                # Use aisuite's standardized response format
                # handle tool calls
                reasoning = None
                requested_tools = None
                if hasattr(response, "choices") and hasattr(response.choices[0].message, "tool_calls"):
                    requested_tools = response.choices[0].message.tool_calls
                    reasoning = response.choices[0].finish_reason
                elif hasattr(response, "reasoning_content"):
                    reasoning = response.reasoning_content
                elif hasattr(response, "choices") and hasattr(response.choices[0].message, "reasoning_content"):
                    reasoning = response.choices[0].message.reasoning_content

                content = response.choices[0].message.content if hasattr(response, 'choices') else response.content
                
                if requested_tools:
                    # Format tool calls into a readable list
                    tool_list = []
                    for tool in requested_tools:
                        tool_info = f"{tool.function.name}: {tool.function.arguments}"
                        tool_list.append(tool_info)

                    content = f"{reasoning}:\n\n" + "\n".join(tool_list)

                # Log the response from the LLM
                self.logger.info(f"RESPONSE FROM {self.model}:\n{'-' * 80}\n{content}\n{'-' * 80}")
                
                # Log usage statistics if available
                if hasattr(response, "usage"):
                    usage = response.usage
                    if hasattr(usage, 'prompt_tokens') and \
                        hasattr(usage, 'completion_tokens') and \
                            hasattr(usage, 'total_tokens'):
                        self.logger.info(
                            f"USAGE: prompt_tokens={usage.prompt_tokens}, "
                            f"completion_tokens={usage.completion_tokens}, "
                            f"total_tokens={usage.total_tokens}"
                        )

                return {
                    "content": content,
                    "model": self.model,  # Use our model string since it's guaranteed to exist
                    "usage": getattr(response, "usage", None),
                    # Include any thinking content if present
                    "reasoning": reasoning,
                    "requested_tools": requested_tools,
                }

            except (APIConnectionError, RateLimitError) as e:
                if attempt >= max_retries:
                    raise e
                delay = self.retry_delay * (2**attempt)
                self.logger.warning("Retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, max_retries)
                await asyncio.sleep(delay)
            except ValueError as e:
                # Handle configuration/model format errors
                raise e
            except AttributeError as e:
                # Handle response structure mismatches
                self.logger.error("Unexpected response structure from provider: %s", str(e))
                raise LLMError(f"Unexpected response structure: {str(e)}") from e

        raise LLMError("Max retries exceeded")

    def with_mock_llm_call(self, mock_llm_call: Union[bool, Callable[[Dict[str, Any]], Dict[str, Any]]]) -> 'LLMResource':
        """Set the mock LLM call function."""
        if isinstance(mock_llm_call, Callable) or isinstance(mock_llm_call, bool):
            self._mock_llm_call = mock_llm_call
        else:
            raise ValueError("mock_llm_call must be a Callable or a boolean")

        return self

    async def _mock_llm_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock response echoing the prompt."""
        prompt = request.get('prompt', '')
        return {
            "content": f"Echo: {prompt}",
            "model": self.model,
            "usage": None,
            "reasoning": None,
            "requested_tools": None,
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client = None

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains prompt."""
        return "prompt" in request
