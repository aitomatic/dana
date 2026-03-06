# Error Patterns Reference

## Timeline error indicators

Search for these in timeline entries:

| Indicator | Meaning |
|-----------|---------|
| `"type": "unknown_tool_call"` | Tool result with unrecognized type (e.g., `execution_error`) |
| `"type": "failed_tool_call"` | Explicitly failed tool call |
| `"success": false` | Tool execution error |
| `"Error:"` in content | Error message from `_create_tool_error` |
| Missing `tool_call_id` | Tool result not linked to its call |

## Cross-phase causation checklist

Errors often manifest in one phase but originate in another:

### ACT → THINK failures
- `_act_async` stores error with wrong entry type → `_timeline_entry_to_native_message` converts to wrong role → next `_think_async` call to LLM fails
- `_create_tool_error` returns `type="execution_error"` → falls to `else` in `_act_async` → `UNKNOWN_TOOL_CALL` → may convert to `role="assistant"` instead of `role="tool"`

### THINK → ACT failures
- `_think_async` parses tool_calls from LLM → tool_calls have invalid arguments → `_act_async` executes and gets TypeError

### tool_call_id contract
Every `tool_call_id` in an assistant message (`role="assistant"` with `tool_calls`) MUST have a matching `role="tool"` response. Violation causes: `"tool_call_ids did not have response messages: <id>"`

To verify: collect all tool_call_ids from assistant messages, collect all tool_call_ids from tool messages, assert the difference is empty.

## Type → entry_type mapping in `_act_async`

```
tool_result["type"] == "agent"       → SUB_AGENT_RESPONSE  → role="assistant"
tool_result["type"] == "resource"    → RESOURCE_RESULT      → role="tool" ✓
tool_result["type"] == "workflow"    → WORKFLOW_RESULT       → role="tool" ✓
tool_result["type"] == anything else → UNKNOWN_TOOL_CALL     → role="tool" if tool_call_id present (fixed)
```

## Entry type → native message role mapping

```
USER_MESSAGE                         → role="user"
TIMELINE_SUMMARY, CONTEXT           → role="system"
RESOURCE_RESULT, WORKFLOW_RESULT     → role="tool" (with tool_call_id)
TOOL_CALL                           → role="assistant" (with tool_calls array)
UNKNOWN_TOOL_CALL, FAILED_TOOL_CALL → role="tool" if tool_call_id present, else role="assistant"
Everything else                      → role="assistant"
```

## TimelineEntryType enum values

```
USER_MESSAGE, AGENT_RESPONSE, AGENT_THOUGHTS, TOOL_CALL,
FAILED_TOOL_CALL, SUB_AGENT_RESPONSE, RESOURCE_RESULT,
WORKFLOW_RESULT, UNKNOWN_TOOL_CALL, AGENT_LEARNING,
TIMELINE_SUMMARY, CONTEXT, TODO_LIST
```

## `_create_tool_error` behavior

Located in `tool_caller.py` (WARCaller class):
```python
def _create_tool_error(self, tool_type: str, target: str, error_message: str) -> dict:
    return {"type": tool_type, "target": target, "result": f"Error: {error_message}", "success": False}
```

The `tool_type` parameter is typically `"execution_error"` for caught exceptions, which does NOT match `"resource"`, `"agent"`, or `"workflow"` — so it falls to the `else` branch in `_act_async`.

## Dual-format timeline pitfall

`CompressedTimeline` stores both `entries` (legacy) and `native_messages`. When `load_from_entries()` receives both, pre-saved `native_messages` take precedence and bypass `_timeline_entry_to_native_message`. To test conversion fixes, load entries only (omit `native_messages`).

## STARAgent.__getattr__ trap

STARAgent has a `__getattr__` that catches ALL unknown attribute access and returns a function. Use `agent.__dict__.get("attr")` instead of `getattr(agent, "attr", None)` to safely check for instance attributes.
