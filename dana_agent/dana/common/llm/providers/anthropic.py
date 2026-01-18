"""
Anthropic Provider Implementation
"""

import anthropic
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider using the official Anthropic library."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-sonnet-20240229", base_url: str | None = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use
            base_url: Custom base URL (not used with official client)
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("anthropic")

        if not self.api_key:
            config = config_manager.get_provider_config("anthropic")
            api_key_env = config.get("api_key_env") if config else "ANTHROPIC_API_KEY"
            raise ValueError(f"Anthropic API key not found. Set {api_key_env} environment variable.")

        # Use official Anthropic client with prompt caching beta header
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key, default_headers={"anthropic-beta": "prompt-caching-2024-07-31"})

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Anthropic and get a response."""
        try:
            # Convert our message format to Anthropic format
            system_message = None
            system_cache_control = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                    system_cache_control = msg.cache_control
                elif msg.role == "user":
                    if msg.cache_control:
                        user_msg = {"role": "user", "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}]}
                    else:
                        user_msg = {"role": "user", "content": msg.content}
                    anthropic_messages.append(user_msg)
                elif msg.role == "assistant":
                    if msg.cache_control:
                        assistant_msg = {
                            "role": "assistant",
                            "content": [{"type": "text", "text": msg.content, "cache_control": msg.cache_control}],
                        }
                    else:
                        assistant_msg = {"role": "assistant", "content": msg.content}
                    anthropic_messages.append(assistant_msg)

            # Prepare request parameters
            request_kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens") or 4096,
            }

            # Add system message if present (with cache_control support)
            if system_message:
                if system_cache_control:
                    request_kwargs["system"] = [{"type": "text", "text": system_message, "cache_control": system_cache_control}]
                else:
                    request_kwargs["system"] = system_message

            # Call Anthropic API
            response = await self.client.messages.create(**request_kwargs)

            # Convert response to our format
            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }
                if response.usage
                else None,
                finish_reason=response.stop_reason,
            )

        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
