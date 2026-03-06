"""
Timeline package — chronological record of agent interactions.

Exports the core timeline classes and types used across the dana agent.
"""

from .timeline import (
    Timeline,
    TimelineConfig,
    TimelineEntry,
    TimelineEntryType,
    TimelineProtocol,
)
from .compressed_timeline import CompressedTimeline
from .native_message import NativeMessage, NativeMessageRole, NativeToolCall
from .token_limiting_helpers import apply_token_limit_to_messages, estimate_messages_tokens
from .compression_engine import CompressionMixin

__all__ = [
    "Timeline",
    "TimelineConfig",
    "TimelineEntry",
    "TimelineEntryType",
    "TimelineProtocol",
    "CompressedTimeline",
    "NativeMessage",
    "NativeMessageRole",
    "NativeToolCall",
    "apply_token_limit_to_messages",
    "estimate_messages_tokens",
    "CompressionMixin",
]
