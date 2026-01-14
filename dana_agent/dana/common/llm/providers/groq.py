"""
Groq Provider Implementation
"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class GroqProvider(LLMProvider):
    """Groq API provider for fast inference."""

    @property
    def supports_native_tools(self) -> bool:
        """Groq supports native function/tool calling via OpenAI-compatible API.

        NOTE: Disabled until we properly implement the tool result flow.
        See OpenAIProvider.supports_native_tools for details.
        """
        return False

    def __init__(self, api_key: str | None = None, model: str = "llama3-8b-8192", base_url: str | None = None):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model to use
            base_url: Custom base URL
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("groq")

        if not self.api_key:
            config = config_manager.get_provider_config("groq")
            api_key_env = config.get("api_key_env") if config else "GROQ_API_KEY"
            raise ValueError(f"Groq API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("groq")

        # Use OpenAI client with Groq endpoint
        client_kwargs = {"api_key": self.api_key, "base_url": self.base_url}

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages to Groq and get a response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool schemas for native function calling
            **kwargs: Additional parameters passed to the API
        """
        try:
            # Convert our message format to OpenAI format
            openai_messages = []
            for msg in messages:
                if msg.role == "system":
                    openai_messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    openai_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    openai_messages.append({"role": "assistant", "content": msg.content})

            # Build request parameters
            request_kwargs = {
                "model": self.model,
                "messages": openai_messages,
                **kwargs
            }

            # Add tools if provided
            if tools:
                request_kwargs["tools"] = tools
                request_kwargs["tool_choice"] = "auto"

            # Call Groq API (OpenAI-compatible)
            response = await self.client.chat.completions.create(**request_kwargs)

            # Convert response to our format
            choice = response.choices[0]
            message = choice.message

            # Handle both text responses and function calls
            if hasattr(message, "tool_calls") and message.tool_calls and choice.finish_reason == "tool_calls":
                # Pass through function calls for base_agent to handle
                content = ""
                tool_calls = message.tool_calls
            else:
                # Standard text response
                content = message.content or ""
                tool_calls = None

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error("Groq API error", error=str(e))
            raise
