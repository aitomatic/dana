"""
Anthropic-Like Provider Implementation

Connects to an Anthropic-compatible API at a custom endpoint.
Reuses all Anthropic chat logic (message conversion, tool calling, JSON mode, caching)
but reads credentials from ANTHROPIC_LIKE_API_KEY and ANTHROPIC_LIKE_BASE_URL.
"""

import anthropic
import structlog

from ...config import config_manager
from .anthropic import AnthropicProvider


logger = structlog.get_logger()


class AnthropicLikeProvider(AnthropicProvider):
    """Provider for Anthropic-compatible APIs hosted at custom endpoints."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514", base_url: str | None = None):
        """
        Initialize Anthropic-Like provider.

        Args:
            api_key: API key (defaults to ANTHROPIC_LIKE_API_KEY env var)
            model: Model to use
            base_url: Custom base URL (defaults to ANTHROPIC_LIKE_BASE_URL env var)
        """
        self.model = model

        # Get API key from parameter, env var, or config
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = config_manager.get_provider_api_key("anthropic_like")

        if not self.api_key:
            config = config_manager.get_provider_config("anthropic_like")
            api_key_env = config.get("api_key_env") if config else "ANTHROPIC_LIKE_API_KEY"
            raise ValueError(f"Anthropic-Like API key not found. Set {api_key_env} environment variable.")

        # Get base URL from parameter, env var, or config
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config_manager.get_provider_base_url("anthropic_like")

        if not self.base_url:
            config = config_manager.get_provider_config("anthropic_like")
            base_url_env = config.get("base_url_env") if config else "ANTHROPIC_LIKE_BASE_URL"
            raise ValueError(f"Anthropic-Like base URL not found. Set {base_url_env} environment variable.")

        # Use Anthropic client pointed at the custom endpoint
        self.client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        )
