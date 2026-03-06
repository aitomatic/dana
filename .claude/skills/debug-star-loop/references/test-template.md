# Test Template for STARAgent Loop Debugging

## DanaCodingAgent instantiation

```python
from dana.core.agent.builtin_agents.dana_coding_agent import DanaCodingAgent
from dana.core.agent.compressed_timeline import CompressedTimeline
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType

agent = DanaCodingAgent(
    agent_id="test-<descriptive-name>",
    agent_type="dana_coding_agent",
    llm_provider="anthropic_like",
    model="kimi-k2-thinking-turbo",
    cwd="/tmp",
)
```

## Loading timeline fixture

```python
import json
from pathlib import Path

TIMELINE_PATH = Path(__file__).resolve().parent / "fixtures" / "<fixture-name>.json"

def _load_timeline_data() -> dict:
    if not TIMELINE_PATH.exists():
        pytest.skip(f"Timeline fixture not found: {TIMELINE_PATH}")
    with open(TIMELINE_PATH) as f:
        return json.load(f)
```

## Deterministic replay pattern: ACT phase

Extract tool_calls from a timeline entry (what `_think_async` produced) and feed to `_act_async`:

```python
import asyncio

def test_act_phase_error(self):
    data = _load_timeline_data()

    # Find the tool_call entry before the error
    tool_call_entry = None
    for entry in data["entries"]:
        if entry.get("type") == "tool_call":
            tool_call_entry = entry
    tool_calls = tool_call_entry["tool_calls"]

    agent = DanaCodingAgent(
        agent_id="test-act-replay",
        agent_type="dana_coding_agent",
        llm_provider="anthropic_like",
        model="kimi-k2-thinking-turbo",
        cwd="/tmp",
    )

    # Simulate _think_async adding the tool_call entry
    agent._timeline.add_entry(
        TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
            tool_calls=tool_calls,
        )
    )

    # Build trace_thoughts as _think_async would produce
    trace_thoughts = {
        "response": "...",
        "tool_calls": tool_calls,
        "done": False,
    }

    # Run _act_async — deterministic, no LLM call
    result = asyncio.run(agent._act_async(trace_thoughts))

    # Assert on the timeline entries created by _act_async
    # ...
```

## Testing native message conversion

```python
def test_entry_converts_to_correct_role(self):
    data = _load_timeline_data()

    # Find the error entry
    error_entry_dict = next(
        e for e in data["entries"]
        if e.get("type") == "unknown_tool_call" and e.get("tool_call_id")
    )
    entry = TimelineEntry.from_dict(error_entry_dict)

    agent = DanaCodingAgent(
        agent_id="test-conversion",
        agent_type="dana_coding_agent",
        llm_provider="anthropic_like",
        model="kimi-k2-thinking-turbo",
        cwd="/tmp",
    )
    compressed_timeline: CompressedTimeline = agent._timeline

    native_msg = compressed_timeline._timeline_entry_to_native_message(entry)

    assert native_msg.role == "tool"
    assert native_msg.tool_call_id == entry.tool_call_id
```

## Full round-trip test

Verify all tool_call_ids have matching tool results:

```python
def test_all_tool_call_ids_have_responses(self):
    data = _load_timeline_data()

    agent = DanaCodingAgent(
        agent_id="test-roundtrip",
        agent_type="dana_coding_agent",
        llm_provider="anthropic_like",
        model="kimi-k2-thinking-turbo",
        cwd="/tmp",
    )

    # Load entries only (not pre-saved native_messages) to test conversion
    agent._timeline.load_from_entries(entries=data["entries"])

    native_messages = agent._timeline._native_messages

    # Collect tool_call_ids from assistant messages
    expected = set()
    for msg in native_messages:
        if msg.role == "assistant" and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.id:
                    expected.add(tc.id)

    # Collect tool_call_ids from tool messages
    responded = set()
    for msg in native_messages:
        if msg.role == "tool" and msg.tool_call_id:
            responded.add(msg.tool_call_id)

    missing = expected - responded
    assert not missing, f"Unmatched tool_call_ids: {missing}"
```

## Reference: existing regression test

See `tests/regression/test_tool_call_error_timeline.py` for a complete working example with 5 tests covering:
- Timeline fixture validation
- `_act_async` error handling with tool_call_id preservation
- `_timeline_entry_to_native_message` role conversion
- Error feedback flow (bad kwargs → error → timeline → native message)
- Full round-trip tool_call_id matching
