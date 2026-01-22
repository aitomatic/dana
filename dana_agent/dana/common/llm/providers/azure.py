"""
Azure Provider Implementation
"""

from openai import AsyncAzureOpenAI
import structlog

from ...config import config_manager
from ..types import LLMMessage, LLMProvider, LLMResponse


logger = structlog.get_logger()


class AzureProvider(LLMProvider):
    """Azure OpenAI provider."""

    def __init__(
        self, api_key: str | None = None, model: str = "gpt-35-turbo", base_url: str | None = None, api_version: str | None = None
    ):
        """
        Initialize Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_OPENAI_API_KEY env var)
            model: Model/deployment name to use
            base_url: Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com)
            api_version: Azure OpenAI API version
        """
        self.model = model
        self.deployment_name = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("azure")

        if not self.api_key:
            config = config_manager.get_provider_config("azure")
            api_key_env = config.get("api_key_env") if config else "AZURE_OPENAI_API_KEY"
            raise ValueError(f"Azure OpenAI API key not found. Set {api_key_env} environment variable.")

        # Get base URL (Azure endpoint) from parameter, env var, or config
        if base_url:
            azure_endpoint = base_url
        else:
            azure_endpoint = config_manager.get_provider_base_url("azure")

        if not azure_endpoint:
            raise ValueError("Azure OpenAI endpoint URL not found. Set AZURE_OPENAI_API_URL environment variable.")

        # Clean up the endpoint URL - remove trailing slashes
        azure_endpoint = azure_endpoint.rstrip("/")

        # Get API version from parameter, env var, or config
        if api_version:
            self.api_version = api_version
        else:
            self.api_version = config_manager.get_provider_api_version("azure") or "2024-02-15-preview"

        # Use the dedicated Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=azure_endpoint,
            api_version=self.api_version,
        )

    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to Azure OpenAI and get a response."""
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

            # Call Azure OpenAI API
            response = await self.client.chat.completions.create(model=self.deployment_name, messages=openai_messages, **kwargs)

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
            logger.error("Azure OpenAI API error", error=str(e))
            raise
