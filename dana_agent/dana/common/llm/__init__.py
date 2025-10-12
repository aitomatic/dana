"""Adana LLM Library - Public API."""

from .llm import LLM
from .types import LLMMessage, LLMResponse, ProviderError


# Debug logging functions
try:
    from .debug_logger import disable_debug_logging, enable_debug_logging, get_debug_logger

    def enable_llm_debug_logging():
        """Enable comprehensive LLM debug logging to ~/.dana/logs/."""
        enable_debug_logging()

    def disable_llm_debug_logging():
        """Disable LLM debug logging."""
        disable_debug_logging()

    def get_llm_debug_stats():
        """Get debug logging statistics."""
        return get_debug_logger().get_log_stats()

    __all__ = [
        "LLM",
        "LLMMessage",
        "LLMResponse",
        "ProviderError",
        "enable_llm_debug_logging",
        "disable_llm_debug_logging",
        "get_llm_debug_stats",
    ]

except ImportError:
    # Debug logging not available
    def enable_llm_debug_logging():
        """Debug logging not available."""
        pass

    def disable_llm_debug_logging():
        """Debug logging not available."""
        pass

    def get_llm_debug_stats():
        """Debug logging not available."""
        return {"error": "Debug logging not available"}

    __all__ = [
        "LLM",
        "LLMMessage",
        "LLMResponse",
        "ProviderError",
        "enable_llm_debug_logging",
        "disable_llm_debug_logging",
        "get_llm_debug_stats",
    ]
