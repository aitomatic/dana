"""
Adana Common - Shared utilities and libraries

Common functionality used across the Adana project.
"""

__all__ = ["LLM", "LLMMessage", "LLMResponse"]


def __getattr__(name: str):
    if name in __all__:
        from .llm import LLM, LLMMessage, LLMResponse

        return {"LLM": LLM, "LLMMessage": LLMMessage, "LLMResponse": LLMResponse}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
