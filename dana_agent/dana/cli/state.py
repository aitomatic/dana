"""Render state management for the Rich CLI renderer."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RenderState:
    """Tracks the current render state for the CLI renderer.

    Holds phase info, agent context, tool results, and UI state
    (expand/collapse, selection) for the Rich terminal display.
    """

    # Current STAR phase
    current_phase: str = ""

    # Agent context
    current_agent_id: str = ""
    current_model: str = ""
    current_turn: int = 0
    max_turns: int = 0

    # Tool results - current turn (interactive/recent)
    current_turn_results: list[Any] = field(default_factory=list)

    # Tool results - historical (collapsed/dimmed)
    historical_results: list[Any] = field(default_factory=list)

    # UI state for result panel navigation
    expanded_indices: set[int] = field(default_factory=set)
    selected_index: int = -1

    # Todo/progress tracking
    todo_items: list[Any] = field(default_factory=list)
