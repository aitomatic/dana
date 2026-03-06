"""OpenAI-specific AgentRuntime."""

from __future__ import annotations

from .codec.codec_with_native_tool_use import CodecRuntimeWithNativeToolUse


class OpenAIRuntime(CodecRuntimeWithNativeToolUse):
    """Runtime for OpenAI models (GPT family).

    Inherits all behaviour from CodecRuntimeWithNativeToolUse.
    Override methods here when OpenAI-specific behaviour is needed.
    """
