"""
OpenAI Provider Implementation
"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    @property
    def supports_native_tools(self) -> bool:
        """OpenAI supports native function/tool calling.

        NOTE: Disabled until we properly implement the tool result flow.
        OpenAI requires tool results to be sent back with role="tool" and
        tool_call_id, but we currently send them as role="assistant" which
        confuses the LLM and causes excessive retries.

        TODO: Implement proper native tool result flow:
        1. Store tool_call_id when parsing native tool calls
        2. Send tool results with role="tool" and matching tool_call_id
        3. Include the assistant message with tool_calls in the conversation
        """
        return False

    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo", base_url: str | None = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use
            base_url: Custom base URL (for OpenAI-compatible endpoints)
        """
        self.model = model
        self.base_url = base_url

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("openai")

        if not self.api_key:
            config = config_manager.get_provider_config("openai")
            api_key_env = config.get("api_key_env") if config else "OPENAI_API_KEY"
            raise ValueError(f"OpenAI API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("openai")

        # Initialize client
        client_kwargs = {"api_key": self.api_key, "base_url": self.base_url}

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        """Send messages to OpenAI and get a response.

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

            # Call OpenAI API
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
            logger.error("OpenAI API error", error=str(e))
            raise
