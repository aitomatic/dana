"""
Provider Factory

Factory function for creating provider instances.
"""

from ...config import config_manager
from ..types import ConfigurationError, LLMProvider
from .openai import OpenAIProvider


def create_provider(provider_name: str, model: str | None = None, **kwargs) -> LLMProvider:
    """Create a provider instance by name.

    Args:
        provider_name: Name of the provider ('openai', 'anthropic', 'azure', etc.)
        model: Model to use (defaults to provider's default)
        **kwargs: Additional provider-specific arguments

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported or not available
    """
    import os

    config = config_manager.get_provider_config(provider_name)
    if not config:
        available = config_manager.get_available_providers()
        raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")

    # Use model in this order: parameter > env var > config default
    model_env_var = f"{provider_name.upper()}_MODEL"
    env_model = os.getenv(model_env_var)

    if model is None:
        model = env_model or config.get("default_model")

    model = model or "gpt-3.5-turbo"

    if provider_name == "openai":
        return OpenAIProvider(model=model, **kwargs)
    elif provider_name == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider(model=model, **kwargs)
    elif provider_name == "anthropic_like":
        from .anthropic_like import AnthropicLikeProvider

        return AnthropicLikeProvider(model=model, **kwargs)
    elif provider_name == "azure":
        from .azure import AzureProvider

        return AzureProvider(model=model, **kwargs)
    elif provider_name == "gemini":
        from .gemini import GeminiProvider

        return GeminiProvider(model=model, **kwargs)
    else:
        # For other providers, try OpenAI-compatible client
        base_url = config.get("base_url")
        api_key = config_manager.get_provider_api_key(provider_name)

        if not api_key and config.get("api_key_env"):
            raise ConfigurationError(f"API key not found for {provider_name}. Set {config['api_key_env']} environment variable.")

        if not api_key:
            raise ConfigurationError(f"API key not found for {provider_name}. No API key environment variable configured.")

        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url, **kwargs)
