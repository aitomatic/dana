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

        # Use official Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Anthropic and get a response."""
        try:
            # Convert our message format to Anthropic format
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                elif msg.role == "user":
                    anthropic_messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": msg.content})

            # Prepare request parameters
            request_kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 1000),
            }

            # Add system message if present
            if system_message:
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
