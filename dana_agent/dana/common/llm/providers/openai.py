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

        The tool result flow is now properly implemented:
        1. tool_call_id is stored when parsing native tool calls
        2. Tool results are sent with role="tool" and matching tool_call_id
        3. Assistant messages with tool_calls are properly formatted
        """
        return True

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
                elif msg.role == "tool":
                    # Tool result message - requires tool_call_id
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    })
                elif msg.role == "assistant":
                    # Check if this assistant message has native tool_calls
                    if msg.tool_calls:
                        # Format tool_calls for OpenAI API
                        formatted_tool_calls = []
                        for tc in msg.tool_calls:
                            formatted_tool_calls.append({
                                "id": tc.get("tool_call_id", ""),
                                "type": "function",
                                "function": {
                                    "name": tc.get("function", ""),
                                    "arguments": str(tc.get("arguments", {})),
                                },
                            })
                        openai_messages.append({
                            "role": "assistant",
                            "content": msg.content or None,
                            "tool_calls": formatted_tool_calls,
                        })
                    else:
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
            # Note: finish_reason can be "tool_calls" or "stop" depending on model version
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Pass through function calls for base_agent to handle
                content = message.content or ""
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
