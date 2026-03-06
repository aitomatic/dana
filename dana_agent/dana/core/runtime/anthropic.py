"""Anthropic-specific AgentRuntime."""

from __future__ import annotations

from .codec.codec_with_native_tool_use import CodecRuntimeWithNativeToolUse


class AnthropicRuntime(CodecRuntimeWithNativeToolUse):
    """Runtime for Anthropic models (Claude family).

    Inherits all behaviour from CodecRuntimeWithNativeToolUse.
    Override methods here when Anthropic-specific behaviour is needed.
    """
