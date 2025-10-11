"""
Hugging Face Provider Implementation
"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference API provider."""

    def __init__(self, api_key: str | None = None, model: str = "microsoft/DialoGPT-medium", base_url: str | None = None):
        """
        Initialize Hugging Face provider.

        Args:
            api_key: Hugging Face API key (defaults to HF_TOKEN env var)
            model: Model to use
            base_url: Custom base URL
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("huggingface")

        if not self.api_key:
            config = config_manager.get_provider_config("huggingface")
            api_key_env = config.get("api_key_env") if config else "HF_TOKEN"
            raise ValueError(f"Hugging Face API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("huggingface")

        # Use OpenAI client with Hugging Face endpoint
        # Configure retry behavior: 2 retries max (default is 2, but making it explicit)
        # The OpenAI client will retry on 429 (rate limit) and 5xx (server errors)
        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "max_retries": 2,  # Retry up to 2 times on transient errors
            "timeout": 60.0,  # 60 second timeout per request
        }

        self.client = AsyncOpenAI(**client_kwargs)

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Hugging Face and get a response."""
        import httpx

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

            # Call Hugging Face API (OpenAI-compatible)
            response = await self.client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Handle different response formats
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                message = choice.message

                # Check if this is a function calling response
                if hasattr(message, "tool_calls") and message.tool_calls and choice.finish_reason == "tool_calls":
                    # Pass through function calls for base_agent to handle
                    content = ""  # Empty content when using function calls
                    tool_calls = message.tool_calls
                else:
                    # Standard text response
                    content = message.content or ""
                    tool_calls = None

                model = response.model
                usage = (
                    {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None
                )
                finish_reason = choice.finish_reason
            else:
                # Handle string response or other formats
                content = str(response) if response else ""
                model = self.model
                usage = None
                finish_reason = None
                tool_calls = None

            return LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
            )

        except httpx.HTTPStatusError as e:
            logger.error("Hugging Face HTTP error", status_code=e.response.status_code, error=str(e))
            raise
        except Exception as e:
            logger.error("Hugging Face API error", error=str(e), error_type=type(e).__name__)
            raise
