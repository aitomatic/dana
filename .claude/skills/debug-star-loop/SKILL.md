---
name: debug-star-loop
description: Debug STARAgent loop failures using saved timeline JSON files. Use when the agent loop crashes, tool calls fail, the LLM API rejects messages, or timeline entries are malformed. Triggers on errors like "tool_call_ids did not have response messages", TypeError in tool execution, or any STAR loop crash.
---

# Debug STARAgent Loop

Debug agent loop failures by replaying saved timeline JSON files deterministically — no LLM calls needed.

## Input

Error description or context: $ARGUMENTS

## Procedure

Follow these steps in order. Do NOT skip steps.

### Step 1: Find error timelines

Search `.dana/` for timeline JSON files related to the error:

```bash
find .dana -name "timeline.json" -path "*/events/*" | head -20
```

Timelines live at: `.dana/dana_agent/NativeToolsCodec/<agent-id>/events/<session>/timeline.json`

Look for error indicators in the timeline entries. For details on what to look for, see [references/error-patterns.md](references/error-patterns.md).

### Step 2: Analyze the timeline

Read the timeline and identify:
1. **Which entry has the error** — scan for `unknown_tool_call`, `failed_tool_call`, error messages
2. **Which STAR phase it belongs to** — SEE, THINK, or ACT
3. **Cross-phase causation** — errors often manifest in one phase but originate in another. For the full analysis checklist, see [references/error-patterns.md](references/error-patterns.md).

### Step 3: Copy timeline to test fixtures

```bash
cp <timeline-path> dana_agent/tests/regression/fixtures/<descriptive-name>.json
```

### Step 4: Create deterministic replay tests

Create tests in `dana_agent/tests/regression/` that:
- Load the timeline fixture
- Extract the output of the phase BEFORE the error (e.g., `tool_calls` from a `tool_call` entry)
- Feed it directly to the failing phase method (e.g., `_act_async`)
- No LLM calls — deterministic replay only

For the test template and DanaCodingAgent instantiation pattern, see [references/test-template.md](references/test-template.md).

### Step 5: Narrow down root cause

If Step 4 doesn't pinpoint the exact root cause, create additional targeted tests:
- Test `_timeline_entry_to_native_message` conversion directly
- Test `_create_tool_error` output format
- Test the type → entry_type mapping in `_act_async`
- Test `load_from_entries` with and without pre-saved `native_messages`

Keep adding tests until you are 100% sure about the root cause.

### Step 6: Report findings

Tell the user:
- **Root cause**: What exactly is wrong and why
- **Phase(s) involved**: Which STAR phases and cross-phase interactions
- **Code locations**: Exact `file_path:line_number` references
- **Proposed fix**: With rationale
- **Design principle**: The system must be robust to tool failures. Don't silently mask errors — let tools fail, capture errors with correct `tool_call_id`, feed back as `role="tool"` so the LLM can self-correct.

## Key files

| File | Contains |
|------|----------|
| `dana/core/agent/star_agent.py` | `_act_async`, `_think_async`, `_see` |
| `dana/core/agent/compressed_timeline.py` | `_timeline_entry_to_native_message`, `load_from_entries` |
| `dana/core/agent/timeline.py` | `TimelineEntry`, `TimelineEntryType` enum |
| `dana/core/runtime/base.py` | `_create_tool_error`, `_execute_single_call_async`, `_validate_n_cast_method_arguments` |
| `dana/core/agent/components/tool_caller.py` | `_create_tool_error` (WARCaller) |
| `dana/core/agent/builtin_agents/dana_coding_agent.py` | `DanaCodingAgent` |
| `tests/regression/` | Existing regression tests and fixtures |
