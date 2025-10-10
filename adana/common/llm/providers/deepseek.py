"""
DeepSeek LLM Provider

Supports DeepSeek's API for chat completions.
"""

import os

from ..types import LLMMessage, LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider implementation."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str = "deepseek-chat"):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)
            base_url: DeepSeek API base URL (defaults to DEEPSEEK_BASE_URL env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model

        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Send chat messages to DeepSeek API.

        Args:
            messages: List of LLMMessage objects
            **kwargs: Additional parameters for the API call

        Returns:
            LLMResponse object with the generated content
        """
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI library is required for DeepSeek provider. Install with: pip install openai")

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

        # Create OpenAI client with DeepSeek configuration
        client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        try:
            # Call DeepSeek API
            response = await client.chat.completions.create(model=self.model, messages=openai_messages, **kwargs)

            # Extract content from response
            content = response.choices[0].message.content
            if content is None:
                content = ""

            return LLMResponse(content=content, model=self.model, usage=response.usage.model_dump() if response.usage else None)

        except Exception as e:
            error_msg = f"DeepSeek API error: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"Error code: {e.response.status_code} - {error_detail}"
                except Exception:
                    error_msg = f"Error code: {e.response.status_code} - {str(e)}"

            raise Exception(error_msg)

    def get_available_models(self) -> list[str]:
        """Get list of available DeepSeek models."""
        return ["deepseek-chat", "deepseek-coder", "deepseek-coder-6.7b", "deepseek-coder-33b"]

    def is_available(self) -> bool:
        """Check if DeepSeek provider is available (has API key)."""
        return bool(self.api_key)
