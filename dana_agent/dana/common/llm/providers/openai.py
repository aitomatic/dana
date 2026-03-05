"""OpenAI Provider Implementation"""

from openai import AsyncOpenAI
import structlog

from ...config import config_manager
from .openai_compatible_base import OpenAICompatibleProvider


logger = structlog.get_logger()


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-3.5-turbo", base_url: str | None = None):
        self.model = model

        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("openai")

        if not self.api_key:
            config = config_manager.get_provider_config("openai")
            api_key_env = config.get("api_key_env") if config else "OPENAI_API_KEY"
            raise ValueError(f"OpenAI API key not found. Set {api_key_env} environment variable.")

        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("openai")

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        # Check for use_responses_api config flag
        provider_config = config_manager.get_provider_config("openai")
        self._use_responses_api = provider_config.get("use_responses_api") if provider_config else None
