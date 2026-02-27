"""
STARLoopState — derive STAR loop state from a timeline.

Pure data derivation: no side effects, no LLM calls.
Enables timeline replay and resumption from any checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .timeline import Timeline, TimelineEntry, TimelineEntryType


if TYPE_CHECKING:
    pass


# Entry types that represent tool results added during _act()
_TOOL_RESULT_TYPES = frozenset(
    {
        TimelineEntryType.RESOURCE_RESULT,
        TimelineEntryType.SUB_AGENT_RESPONSE,
        TimelineEntryType.WORKFLOW_RESULT,
        TimelineEntryType.UNKNOWN_TOOL_CALL,
    }
)

# Entry types that represent an assistant "think" output
_ASSISTANT_RESPONSE_TYPES = frozenset(
    {
        TimelineEntryType.AGENT_RESPONSE,
        TimelineEntryType.AGENT_THOUGHTS,
        TimelineEntryType.TOOL_CALL,
    }
)


def _derive_state_from_entries(entries: list[TimelineEntry]) -> dict:
    """
    Walk a list of timeline entries and derive loop state fields.

    Returns a dict with keys: iteration, last_response, last_tool_calls,
    last_tool_results, is_done.
    """
    iteration = 0
    last_response: str | None = None
    last_tool_calls: list[dict] = []
    last_tool_results: list[dict] = []
    is_done = False

    # Track the index of the last TOOL_CALL entry so we can find
    # the tool results that follow it.

    for _i, entry in enumerate(entries):
        et = entry.entry_type

        if et == TimelineEntryType.AGENT_RESPONSE:
            # A terminal response: one complete STAR iteration
            iteration += 1
            last_response = entry.content if isinstance(entry.content, str) else str(entry.content)
            last_tool_calls = []
            last_tool_results = []
            is_done = True  # AGENT_RESPONSE means no more tool calls this turn

        elif et == TimelineEntryType.TOOL_CALL:
            # Starts a new think round that involves tool execution
            iteration += 1
            is_done = False
            last_tool_results = []  # reset; new results will follow

            # Extract tool calls from this entry
            if entry.tool_calls:
                # Native OpenAI format: tool_calls list stored on entry
                last_tool_calls = list(entry.tool_calls)
            else:
                # Legacy XML format: content holds the XML string
                last_tool_calls = [{"content": entry.content}] if entry.content else []

        elif et in _TOOL_RESULT_TYPES:
            # Tool results come after a TOOL_CALL entry
            result: dict = {
                "type": et.value,
                "content": entry.content,
            }
            if entry.tool_call_id is not None:
                result["tool_call_id"] = entry.tool_call_id
            last_tool_results.append(result)

        elif et == TimelineEntryType.AGENT_THOUGHTS:
            # Reasoning text emitted alongside tool calls — does NOT add an iteration
            # (iteration is counted on TOOL_CALL, not AGENT_THOUGHTS)
            pass

    return {
        "iteration": iteration,
        "last_response": last_response,
        "last_tool_calls": last_tool_calls,
        "last_tool_results": last_tool_results,
        "is_done": is_done,
    }


@dataclass
class STARLoopState:
    """
    Derivable from a Timeline — captures the current state of the STAR loop.

    All fields are computed by walking timeline entries; there are no side
    effects and no LLM calls.

    Attributes:
        timeline:          The source Timeline object.
        iteration:         Number of STAR loop iterations completed
                           (each AGENT_RESPONSE or TOOL_CALL batch = 1 iteration).
        last_response:     Content of the last AGENT_RESPONSE entry, or None.
        last_tool_calls:   Tool calls from the last TOOL_CALL entry.
        last_tool_results: Tool results that followed the last TOOL_CALL entry.
        is_done:           True when the last think round produced an AGENT_RESPONSE
                           (no pending tool calls).
    """

    timeline: Timeline
    iteration: int
    last_response: str | None
    last_tool_calls: list[dict] = field(default_factory=list)
    last_tool_results: list[dict] = field(default_factory=list)
    is_done: bool = False

    @classmethod
    def from_timeline(cls, timeline: Timeline) -> STARLoopState:
        """
        Derive state from all entries in the timeline.

        Args:
            timeline: Timeline instance to derive state from.

        Returns:
            STARLoopState reflecting the full timeline history.
        """
        # Exclude ephemeral entries (e.g. CONTEXT) — they are not persisted
        # and not part of the STAR loop logic.
        persistent = [e for e in timeline.timeline if not e.ephemeral]
        state = _derive_state_from_entries(persistent)
        return cls(timeline=timeline, **state)

    @classmethod
    def from_timeline_at_entry(cls, timeline: Timeline, entry_index: int) -> STARLoopState:
        """
        Derive state as of a specific entry index (for replay / debug).

        Only entries[:entry_index] are considered, allowing you to inspect
        what the loop state looked like at any point in the timeline.

        Args:
            timeline:    Timeline instance.
            entry_index: Exclusive upper bound (entries[0:entry_index] are used).
                         Use negative indices for Python-style slicing.

        Returns:
            STARLoopState reflecting timeline state at the given entry index.
        """
        persistent = [e for e in timeline.timeline if not e.ephemeral]

        # Support negative indices
        total = len(persistent)
        if entry_index < 0:
            entry_index = max(0, total + entry_index)
        entry_index = min(entry_index, total)

        subset = persistent[:entry_index]
        state = _derive_state_from_entries(subset)
        return cls(timeline=timeline, **state)
