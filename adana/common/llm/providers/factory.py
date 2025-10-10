"""
Provider Factory

Factory function for creating provider instances.
"""

from ...config import config_manager
from ..types import ConfigurationError, LLMProvider
from .openai import OpenAIProvider


def create_provider(provider_name: str, model: str | None = None, **kwargs) -> LLMProvider:
    """
    Create a provider instance by name.

    Args:
        provider_name: Name of the provider ('openai', 'anthropic', 'ollama', etc.)
        model: Model to use (defaults to provider's default)
        **kwargs: Additional provider-specific arguments

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported or not available
    """
    import os

    # Get provider config
    config = config_manager.get_provider_config(provider_name)
    if not config:
        available = config_manager.get_available_providers()
        raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")

    # Check for model environment variable first
    model_env_var = f"{provider_name.upper()}_MODEL"
    env_model = os.getenv(model_env_var)

    # Use model in this order: parameter > env var > config default
    if model is None:
        model = env_model or config.get("default_model")

    model = model or "gpt-3.5-turbo"

    # Create provider based on name
    if provider_name == "openai":
        return OpenAIProvider(model=model, **kwargs)
    elif provider_name == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider(model=model, **kwargs)
    elif provider_name == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider(model=model, **kwargs)
    elif provider_name == "azure":
        from .azure import AzureProvider

        return AzureProvider(model=model, **kwargs)
    elif provider_name == "groq":
        from .groq import GroqProvider

        return GroqProvider(model=model, **kwargs)
    elif provider_name == "moonshot":
        from .moonshot import MoonshotProvider

        return MoonshotProvider(model=model, **kwargs)
    elif provider_name == "huggingface":
        from .huggingface import HuggingFaceProvider

        return HuggingFaceProvider(model=model, **kwargs)
    elif provider_name == "qwen":
        from .qwen import QwenProvider

        return QwenProvider(model=model, **kwargs)
    elif provider_name == "deepseek":
        from .deepseek import DeepSeekProvider

        return DeepSeekProvider(model=model, **kwargs)
    elif provider_name == "openrouter":
        from .openrouter import OpenRouterProvider

        return OpenRouterProvider(model=model, **kwargs)
    else:
        # For other providers, try to use OpenAI-compatible client
        base_url = config.get("base_url")
        api_key = config_manager.get_provider_api_key(provider_name)

        if not api_key and config.get("api_key_env"):
            raise ConfigurationError(f"API key not found for {provider_name}. Set {config['api_key_env']} environment variable.")

        if not api_key:
            raise ConfigurationError(f"API key not found for {provider_name}. No API key environment variable configured.")

        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url, **kwargs)
