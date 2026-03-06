"""Default fallback AgentRuntime for all other providers."""

from __future__ import annotations

from .base import AgentRuntime


class DefaultRuntime(AgentRuntime):
    """Fallback runtime for providers without a dedicated subclass.

    Uses JSON-based parsing from AgentRuntime (JSONResponseParser).
    No codec — inherits all base behaviour unchanged.
    """
