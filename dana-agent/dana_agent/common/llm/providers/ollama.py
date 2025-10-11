"""
Ollama Provider Implementation
"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class OllamaProvider(LLMProvider):
    """Ollama local provider."""

    def __init__(self, model: str = "llama2", base_url: str | None = None):
        """
        Initialize Ollama provider.

        Args:
            model: Model to use
            base_url: Ollama server URL
        """
        self.model = model

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("ollama")

        # Use OpenAI client with Ollama endpoint
        client_kwargs = {"api_key": "ollama", "base_url": self.base_url}  # Ollama doesn't require real API key

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Ollama and get a response."""
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

            # Call Ollama API (OpenAI-compatible)
            response = await self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Convert response to our format
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
                finish_reason=response.choices[0].finish_reason,
            )

        except Exception as e:
            logger.error("Ollama API error", error=str(e))
            raise
