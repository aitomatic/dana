"""
Timeline replay tests for the Gemini provider.

Loads a recorded timeline, slices it at each LLM call point (tool_call or
agent_response), and runs build_prompt -> call_llm -> parse_response with
the slice. Tests the provider at every stage of a real conversation.

Run:  source /path/to/.env && uv run pytest tests/live/common/llm/providers/test-gemini-timeline-replay.py --live -v -s
"""

import asyncio
import json
from pathlib import Path

import pytest

from dana.core.agent.builtin_agents.dana_coding_agent import DanaCodingAgent
from dana.core.timeline.timeline import Timeline, TimelineEntry, TimelineEntryType


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_PROVIDER = "gemini"
TARGET_MODEL = "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Timeline loading
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TIMELINE_PATH = FIXTURES_DIR / "timeline-6ce36ed2.json"

LLM_OUTPUT_TYPES = {
    TimelineEntryType.TOOL_CALL,
    TimelineEntryType.AGENT_RESPONSE,
}


def load_timeline_from_fixture() -> Timeline:
    """Load the full timeline from fixture JSON."""
    with open(TIMELINE_PATH) as f:
        data = json.load(f)
    timeline = Timeline(max_context_tokens=128000)
    for entry_dict in data.get("entries", []):
        timeline.add_entry(TimelineEntry.from_dict(entry_dict))
    return timeline


def create_agent(
    provider: str = TARGET_PROVIDER,
    model: str = TARGET_MODEL,
) -> DanaCodingAgent:
    """Create a DanaCodingAgent wired to Gemini."""
    return DanaCodingAgent(
        agent_id="test-gemini-replay",
        agent_type="dana_coding_agent",
        llm_provider=provider,
        model=model,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def full_timeline() -> Timeline:
    if not TIMELINE_PATH.exists():
        pytest.skip(f"Timeline fixture not found: {TIMELINE_PATH}")
    return load_timeline_from_fixture()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGeminiTimelineReplay:
    """Replay timeline by slicing at each LLM call point."""

    @pytest.mark.live
    def test_replay_all_turns(self, full_timeline):
        """Slice timeline at each LLM output entry, call Gemini each time."""
        agent = create_agent()
        all_entries = full_timeline.timeline
        call_count = 0

        for i in range(len(all_entries)):
            entry = all_entries[i]
            if entry.entry_type not in LLM_OUTPUT_TYPES:
                continue

            call_count += 1
            sliced = Timeline(max_context_tokens=128000)
            sliced.timeline = all_entries[:i]
            agent._timeline = sliced

            print(f"\n--- LLM call #{call_count} at entry[{i}] ({entry.entry_type.value}), context={i} entries ---")

            llm_messages = agent._runtime.build_prompt(agent, agent._timeline)
            assert len(llm_messages) > 0, f"call #{call_count}: build_prompt returned empty"

            raw = agent._runtime.call_llm(llm_messages)
            assert raw is not None, f"call #{call_count}: call_llm returned None"
            assert raw.content is not None, f"call #{call_count}: response content is None"

            parsed = agent._runtime.parse_response(raw)
            assert parsed is not None, f"call #{call_count}: parse_response returned None"

            print(f"    response: model={raw.model}, len={len(raw.content)}, done={parsed.done}, tool_calls={len(parsed.tool_calls or [])}")

        assert call_count > 0, "No LLM calls were made during replay"
        print(f"\n=== Replay complete: {call_count} LLM calls across {len(all_entries)} entries ===")

    @pytest.mark.live
    def test_stream_all_turns(self, full_timeline):
        """Slice timeline at each LLM output entry, stream from Gemini each time."""
        agent = create_agent()
        all_entries = full_timeline.timeline
        call_count = 0

        async def _stream_one(llm_messages):
            chunks = []
            text_parts = []
            async for chunk in agent._runtime._llm_caller.call_llm_stream(llm_messages):
                chunks.append(chunk)
                if chunk.type == "text_delta" and chunk.content:
                    text_parts.append(chunk.content)
            return chunks, text_parts

        for i in range(len(all_entries)):
            entry = all_entries[i]
            if entry.entry_type not in LLM_OUTPUT_TYPES:
                continue

            call_count += 1
            sliced = Timeline(max_context_tokens=128000)
            sliced.timeline = all_entries[:i]
            agent._timeline = sliced

            llm_messages = agent._runtime.build_prompt(agent, agent._timeline)
            assert len(llm_messages) > 0

            chunks, text_parts = asyncio.run(_stream_one(llm_messages))

            assert len(chunks) > 0
            full_text = "".join(text_parts)
            print(
                f"\n--- Stream #{call_count} at entry[{i}]: "
                f"{len(chunks)} chunks, text_len={len(full_text)}, "
                f"types={set(c.type for c in chunks)}"
            )

        assert call_count > 0, "No streaming calls were made during replay"
        print(f"\n=== Stream replay complete: {call_count} calls ===")
