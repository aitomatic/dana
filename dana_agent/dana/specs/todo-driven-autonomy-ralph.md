# Explicit Done Flag Autonomy - Implementation Spec

**Status: ⚠️ IN PROGRESS**

## Goal

Replace the implicit STAR loop exit condition (empty `tool_calls`) with an explicit `<done>` flag. The loop only exits when `done=true` and `response` has content.

## Demo

### Without Explicit Done Flag (The Problem)
```
User: "What is the MSFT stock price?"
LLM: "I will fetch the stock price from Yahoo Finance..."
     (tool_calls is empty)

Loop exits → Bad response returned to user
```

### With Explicit Done Flag (The Solution)
```
User: "What is the MSFT stock price?"
LLM: <done>false</done>
     <function_call><invoke name="web:search">...</invoke></function_call>
     <response></response>

Loop continues → Tool executed → Eventually:

LLM: <done>true</done>
     <function_call></function_call>
     <response>The price of MSFT is $425.32.</response>

Loop exits → Good response returned to user
```

### What You'll See
- Loop retries when output format is invalid
- Loop continues when `done=false` with function_call
- Loop exits only when `done=true` with response

## Codebase Context

**Files to modify:**

| File | What to change |
|------|----------------|
| `star_agent.py` | Lines 573-695: Replace retry/exit logic in `_think()` |
| `prompt_api.py` | Line 59+: Replace `<autonomous_operation>` with `<output_format>` |
| `tool_caller.py` | `parse_llm_response()`: Add `<done>` parsing |
| `todo.py` | Delete entire file |

**Key integration points:**

```python
# star_agent.py - existing exit mechanism (use this)
self._mark_star_loop_exit(trace_percepts)

# star_agent.py - existing message type (use this)
from dana.common.llm.types import LLMMessage
correction = LLMMessage(role="user", content="...")

# tool_caller.py - existing parser signature (extend, don't change)
def parse_llm_response(self, response) -> tuple[str, str, list]:
    # Add: extract <done> and return it somehow
```

## MVP Requirements

- [x] Update output format to require three sections: `<done>`, `<function_call>`, `<response>`
- [x] Parse `<done>` as boolean (`true` or `false` literal)
- [x] Implement validation:
  - [x] `done=false` + empty function_call → RETRY
  - [x] `done=true` + empty response → RETRY
  - [x] `done=false` + has function_call → CONTINUE
  - [x] `done=true` + has response → EXIT
- [x] Parse failure or missing sections → RETRY with correction message
- [x] Cap retries at 3 per THINK phase
- [x] Cap STAR loop iterations at 10
- [x] Update system prompt with `<output_format>` section
- [x] Delete `todo.py` resource (no longer needed)
- [x] Remove ToDoResource registration from STARAgent

Expected validation logic:

```python
def validate(parsed: dict) -> OutputState:
    done = parsed["done"]  # boolean
    has_call = len(parsed["function_call"].strip()) > 0
    has_response = len(parsed["response"].strip()) > 0

    if not done and not has_call:
        return RETRY
    if done and not has_response:
        return RETRY
    return EXIT if done else CONTINUE
```

Expected output format:

```xml
<done>false</done>
<function_call>
<invoke name="web:search">
<parameter name="query">MSFT stock price</parameter>
</invoke>
</function_call>
<response></response>
```

## Files Implemented

- `dana_agent/dana/core/agent/star_agent.py` ✅ (update _think, add validation)
- `dana_agent/dana/core/knowledge/prompts/prompt_api.py` ✅ (replace autonomous_operation with output_format)
- `dana_agent/dana/core/agent/components/tool_caller.py` ✅ (update parser for new format)
- `dana_agent/dana/core/agent/base_star_agent.py` ✅ (verify exit condition uses new validation)
- `dana_agent/dana/core/resource/todo.py` ✅ (delete file)
- `dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py` ✅ (new test file)

## Tests Required

Create test file: `dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py`

- [x] `test_exit_when_done_true_with_response` - exits loop, returns response
- [x] `test_continue_when_done_false_with_function_call` - continues loop, executes tool
- [x] `test_retry_when_done_false_no_function_call` - retries with correction
- [x] `test_retry_when_done_true_no_response` - retries with correction
- [x] `test_retry_on_parse_failure` - retries when sections missing
- [x] `test_max_retries_per_iteration` - fails after 3 retries
- [x] `test_max_iterations` - fails after 10 iterations
- [x] `test_simple_task_single_turn` - "2+2" completes in one turn
- [x] `test_prompt_contains_output_format` - system prompt has new format

Command to run tests:
```bash
pytest dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py -v
```

## Success Criteria

1. Loop exits ONLY when `done=true` AND `response` has content
2. Loop continues when `done=false` AND `function_call` has content
3. Invalid outputs trigger retry with correction message
4. No pattern matching in validation logic
5. Backward compatible: existing tool definitions work unchanged
6. All tests pass

## Before Marking Complete

- [ ] All tests pass
- [x] Uses structlog logger (not print)
- [x] Uses LLMMessage class for correction messages
- [x] Follows existing retry loop pattern in _think()
- [x] Uses _mark_star_loop_exit() for exit condition
- [x] No new dependencies added
- [x] No unnecessary complexity (KISS)
- [x] No regex/pattern matching in validation
- [x] Validation is <1ms overhead

## When Complete

Run these commands to verify:
```bash
# Run the new tests
pytest dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py -v

# Run existing star_agent tests to ensure no regressions
pytest dana_agent/dana/core/agent/tests/ -v --ignore=dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py
```

Only if ALL tests pass, write this line to this file:

## References

- PRD: [todo-driven-autonomy-prd.md](./todo-driven-autonomy-prd.md)

<promise>TASK COMPLETE</promise>
