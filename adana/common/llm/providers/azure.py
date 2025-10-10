"""
Azure Provider Implementation
"""

from openai import AsyncOpenAI
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
            model: Model to use
            base_url: Azure OpenAI endpoint URL
            api_version: Azure OpenAI API version
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("azure")

        if not self.api_key:
            config = config_manager.get_provider_config("azure")
            api_key_env = config.get("api_key_env") if config else "AZURE_OPENAI_API_KEY"
            raise ValueError(f"Azure OpenAI API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("azure")

        # Get API version from parameter, env var, or config
        if api_version:
            self.api_version = api_version
        else:
            self.api_version = config_manager.get_provider_api_version("azure")

        # Construct proper Azure OpenAI endpoint URL
        # Azure URLs should be: https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions

        # For deployment-based endpoints, append the model/deployment name to the URL
        if self.base_url and "/deployments" in self.base_url and not self.base_url.endswith("/deployments/"):
            # URL ends with /deployments, append the model name
            self.base_url += f"/{self.model}"
            self.deployment_name = self.model
        elif self.base_url and "/deployments/" in self.base_url:
            # URL already has deployment name, extract it
            deployment_name = self.base_url.split("/deployments/")[1].split("/")[0]
            self.deployment_name = deployment_name
        else:
            self.deployment_name = self.model

        # Ensure URL ends with /
        if self.base_url and not self.base_url.endswith("/"):
            self.base_url += "/"

        # Add API version as query parameter
        if self.api_version and self.base_url:
            separator = "&" if "?" in self.base_url else "?"
            self.base_url += f"{separator}api-version={self.api_version}"

        # Use OpenAI client with Azure endpoint
        client_kwargs = {"api_key": self.api_key, "base_url": self.base_url}
        self.client = AsyncOpenAI(**client_kwargs)

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
