"""
Core event types for Dana agent communication.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Token:
    """Text token emitted by agent during streaming response."""

    text: str


@dataclass
class Status:
    """Status update from agent about current processing step."""

    step: str
    detail: str = ""


@dataclass
class ToolStart:
    """Tool invocation started."""

    name: str
    args: dict


@dataclass
class ToolEnd:
    """Tool invocation completed."""

    name: str
    ok: bool
    ms: int


@dataclass
class Progress:
    """Progress update with percentage complete."""

    pct: float


@dataclass
class FinalResult:
    """Final result of agent processing."""

    data: dict


@dataclass
class Error:
    """Error during agent processing."""

    message: str


@dataclass
class Done:
    """Signal that agent processing is complete."""

    pass


# Union type for all possible agent events
AgentEvent = Union[Token, Status, ToolStart, ToolEnd, Progress, FinalResult, Error, Done]
