"""
LLM Provider Implementations

Concrete implementations of LLM providers for different services.
Providers with optional dependencies (Gemini, Azure) use lazy imports
to avoid ImportError when their SDKs are not installed.
"""

from .anthropic import AnthropicProvider
from .anthropic_like import AnthropicLikeProvider
from .factory import create_provider
from .openai import OpenAIProvider
from .openai_compatible_base import OpenAICompatibleProvider


def __getattr__(name: str):
    """Lazy import providers with optional dependencies."""
    if name == "GeminiProvider":
        from .gemini import GeminiProvider

        return GeminiProvider
    if name == "AzureProvider":
        from .azure import AzureProvider

        return AzureProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AnthropicProvider",
    "AnthropicLikeProvider",
    "AzureProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "OpenAICompatibleProvider",
    "create_provider",
]
