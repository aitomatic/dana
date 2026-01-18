# Todo-Driven Autonomy - Product Requirements Document

## Problem Statement

STARAgent's autonomy loop exits when `tool_calls` is empty. This conflates "LLM didn't call a tool" with "task is done", causing the LLM to output "I will fetch the data..." without actually doing it, and the loop exits with that bad response.

**Root cause:** Implicit exit condition (empty tool_calls) instead of explicit completion signal.

## Solution

Replace implicit exit with explicit `<done>` flag. The LLM must declare completion explicitly.

```
CURRENT (broken):
  tool_calls empty? → EXIT (unreliable)

PROPOSED (fixed):
  done=true + has response? → EXIT (explicit)
```

## Output Format

Every LLM response must contain these three sections:

```xml
<done>true|false</done>

<function_call>
<!-- Tool invocation when done=false, empty when done=true -->
</function_call>

<response>
<!-- Final answer when done=true, empty when done=false -->
</response>
```

**Properties:**
- All three sections required in every response
- `done` is a boolean: literally `true` or `false`
- Structure is always the same (no conditional format)

## Validation Rules

**Two rules. No exceptions.**

| done | function_call | response | Result |
|------|---------------|----------|--------|
| false | empty | * | **RETRY** - "Not done? Must call a tool." |
| false | has content | * | **CONTINUE** - Execute tool, loop continues |
| true | * | empty | **RETRY** - "Done? Must provide answer." |
| true | * | has content | **EXIT** - Return response to user |

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

## Loop Flow

```
┌────────────────────────────────────────────────────────────────┐
│                        STAR LOOP                               │
│                                                                │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐                 │
│   │  THINK  │───▶│ VALIDATE │───▶│   ACT    │                 │
│   │         │    │          │    │          │                 │
│   │ Call LLM│    │ 2 rules  │    │ Execute  │                 │
│   │ Parse   │    │          │    │ tool     │                 │
│   └─────────┘    └────┬─────┘    └────┬─────┘                 │
│                       │               │                        │
│              ┌────────┼────────┐      │                        │
│              ▼        ▼        ▼      │                        │
│           RETRY    EXIT    CONTINUE───┘                        │
│              │        │                                        │
│              │        ▼                                        │
│              │   Return response                               │
│              │   to user                                       │
│              │                                                 │
│              ▼                                                 │
│         Add correction                                         │
│         message, retry                                         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## End-to-End Acceptance Conditions

### Condition 1: Simple Task (Single Turn)

**Input:** "What is 2+2?"

**Expected Output:**
```xml
<done>true</done>
<function_call></function_call>
<response>4</response>
```

**Validation:** `done=true`, `response` has content → **EXIT**, return "4"

---

### Condition 2: Complex Task (Multi-Turn)

**Input:** "What is the current price of MSFT?"

**Turn 1 - LLM Output:**
```xml
<done>false</done>
<function_call>
<invoke name="web:search">
<parameter name="query">MSFT stock price</parameter>
</invoke>
</function_call>
<response></response>
```

**Validation:** `done=false`, `function_call` has content → **CONTINUE**, execute tool

**Turn 2 - After tool returns results, LLM Output:**
```xml
<done>false</done>
<function_call>
<invoke name="web:fetch_url">
<parameter name="url">https://finance.yahoo.com/quote/MSFT</parameter>
</invoke>
</function_call>
<response></response>
```

**Validation:** `done=false`, `function_call` has content → **CONTINUE**, execute tool

**Turn 3 - After fetch returns content, LLM Output:**
```xml
<done>true</done>
<function_call></function_call>
<response>The current price of Microsoft (MSFT) is $425.32.</response>
```

**Validation:** `done=true`, `response` has content → **EXIT**, return response

---

### Condition 3: Invalid - Not Done But No Action

**LLM Output:**
```xml
<done>false</done>
<function_call></function_call>
<response></response>
```

**Validation:** `done=false`, `function_call` empty → **RETRY**

**Correction Message:** "You indicated not done but provided no function_call. Either call a tool or set done=true with a response."

---

### Condition 4: Invalid - Done But No Response

**LLM Output:**
```xml
<done>true</done>
<function_call></function_call>
<response></response>
```

**Validation:** `done=true`, `response` empty → **RETRY**

**Correction Message:** "You indicated done but provided no response. Provide the final answer."

---

### Condition 5: The Old Failure Mode (Now Caught)

**LLM Output:**
```xml
<done>false</done>
<function_call></function_call>
<response>I will now fetch the stock price from Yahoo Finance...</response>
```

**Validation:** `done=false`, `function_call` empty → **RETRY**

The response content is ignored. The rule is simple: `done=false` requires `function_call`.

---

### Condition 6: Parse Failure

**LLM Output:**
```
I will fetch the stock price for you.
```

**Validation:** Missing required sections → **RETRY**

**Correction Message:** "Invalid format. Response must contain <done>, <function_call>, and <response> sections."

## System Prompt

```xml
<output_format>
Every response MUST contain exactly these three sections:

<done>true or false</done>
<function_call>tool invocation OR empty</function_call>
<response>final answer OR empty</response>

RULES:
1. done=false → function_call MUST have content (you must act)
2. done=true → response MUST have content (you must answer)

EXAMPLES:

Task requires tool:
<done>false</done>
<function_call>
<invoke name="web:search">
<parameter name="query">MSFT stock price</parameter>
</invoke>
</function_call>
<response></response>

Task complete:
<done>true</done>
<function_call></function_call>
<response>The price of MSFT is $425.32.</response>
</output_format>
```

## Implementation Changes

| File | Change |
|------|--------|
| `star_agent.py` | Replace exit condition with 2-rule validation |
| `prompt_api.py` | Replace `<autonomous_operation>` with `<output_format>` |
| `tool_caller.py` | Update parser to extract `<done>`, `<function_call>`, `<response>` |
| `todo.py` | Delete (no longer needed) |

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Output format must include three sections: `<done>`, `<function_call>`, `<response>` |
| FR-2 | All three sections required in every response |
| FR-3 | `<done>` must be literal `true` or `false` |
| FR-4 | If `done=false` and `function_call` empty → RETRY |
| FR-5 | If `done=true` and `response` empty → RETRY |
| FR-6 | If `done=false` and `function_call` has content → CONTINUE (execute tool) |
| FR-7 | If `done=true` and `response` has content → EXIT (return to user) |
| FR-8 | Parse failures → RETRY with format correction message |
| FR-9 | Maximum 3 retries per iteration, then fail with error |
| FR-10 | Maximum 10 STAR loop iterations, then fail with error |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Validation overhead < 1ms |
| NFR-2 | No regex or pattern matching in validation |
| NFR-3 | Backward compatible: existing tool definitions unchanged |

## Success Metrics

| Metric | Target |
|--------|--------|
| Autonomy success rate | 100% (no implicit exits) |
| Invalid state detection | 100% (2 rules are exhaustive) |

## Out of Scope

- Todo tracking (can be added later as enhancement)
- Progress reporting
- Re-planning validation
- Pattern matching on response content

## References

- Current implementation: `dana_agent/dana/core/agent/star_agent.py`
- System prompt: `dana_agent/dana/core/knowledge/prompts/prompt_api.py`
- Base STAR loop: `dana_agent/dana/core/agent/base_star_agent.py`
