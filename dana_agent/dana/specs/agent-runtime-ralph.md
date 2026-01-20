# AgentRuntime Refactor - Implementation Spec

**Status: ✅ COMPLETE**

## Goal

Replace the confusing `codec`, `LocalPromptAPI`, `CodecToolCaller`, and `PromptEngineer` abstractions with a single, intuitive concept: **AgentRuntime**.

An AgentRuntime encapsulates all platform-specific behavior for how the agent runs on a target platform (Anthropic, OpenAI, NVIDIA Thor, etc.).

## Demo

### Without AgentRuntime (The Problem)
```python
class MyAgent(STARAgent):
    def __init__(self):
        super().__init__(
            agent_type="my-agent",
            codec=CSXMLCodec,  # What's a codec?
        )

# Internally confusing:
self._prompt_engineer = LocalPromptAPI(...)  # "Local"? "API"? "Engineer"?
self._tool_caller = CodecToolCaller(...)     # Parses AND executes?
```

### With AgentRuntime (The Solution)
```python
class MyAgent(STARAgent):
    def __init__(self):
        super().__init__(
            agent_type="my-agent",
            runtime=AnthropicRuntime(),  # Clear: how the agent runs
        )

# Internally clear:
self._runtime = AnthropicRuntime()
messages = self._runtime.build_prompt(self, timeline)
raw = self._runtime.call_llm(messages)
parsed = self._runtime.parse_response(raw)
results = self._runtime.execute_tools(self, parsed.calls)
```

### What You'll See
- Clean `_think()` method with obvious flow: build_prompt → call_llm → parse_response → execute_tools
- Single `runtime` parameter instead of `codec`
- Platform-specific runtimes: `AnthropicRuntime`, `OpenAIRuntime`, `ThorRuntime`
- Backward compatibility via deprecated `codec` parameter

## Codebase Context

**Key integration points:**

```python
# star_agent.py - current initialization (lines ~50-130)
def __init__(self, ..., codec=CSXMLCodec, ...):
    if codec is not None:
        self._prompt_engineer = LocalPromptAPI(self, codec=codec, ...)
        self._tool_caller = CodecToolCaller(self, codec=codec)
    else:
        self._prompt_engineer = PromptEngineer(self)
        self._tool_caller = ToolCaller(self)

# star_agent.py - current _think() (lines ~580-675)
llm_messages = self._prompt_engineer.build_llm_request(timeline)
llm_response = self.llm_client.chat_response_sync(llm_messages, ...)
response, reasoning, tool_calls, done = self._tool_caller.parse_llm_response(llm_response)
```

**Files to reference for existing patterns:**
- `dana/core/agent/star_agent.py` - STARAgent class
- `dana/core/knowledge/prompts/prompt_api.py` - LocalPromptAPI (absorb into runtime)
- `dana/core/agent/components/tool_caller.py` - CodecToolCaller (absorb into runtime)
- `dana/core/knowledge/prompts/codecs.py` - Codec classes (replace with runtimes)

## MVP Requirements

### Phase 1: Core AgentRuntime Abstraction

- [x] Create `dana/core/runtime/__init__.py` with:
  - [x] `ParsedResponse` dataclass with fields: `done`, `reasoning`, `response`, `tool_calls`
  - [x] `AgentRuntime` abstract base class with methods:
    - [x] `build_prompt(agent, timeline, learned_context=None) -> list[LLMMessage]`
    - [x] `call_llm(messages) -> str`
    - [x] `parse_response(raw) -> ParsedResponse`
    - [x] `execute_tools(agent, tool_calls) -> list[dict]`
    - [x] `get_output_instructions() -> str`

- [x] Create `dana/core/runtime/anthropic.py` with `AnthropicRuntime`:
  - [x] `__init__(model, temperature, max_tokens, llm=None)` - owns LLM instance
  - [x] Migrate prompt building from `LocalPromptAPI`
  - [x] Migrate LLM calling (currently in star_agent._think)
  - [x] Migrate response parsing from `CodecToolCaller.parse_llm_response`
  - [x] Migrate tool execution from `CodecToolCaller.execute_tool_calls`
  - [x] Include done-flag validation logic

- [x] Update `dana/core/agent/star_agent.py`:
  - [x] Add `runtime` parameter to `__init__`
  - [x] Default to `AnthropicRuntime()` when no runtime provided
  - [x] Store as `self._runtime`
  - [x] Update `_think()` to use runtime methods:
    ```python
    messages = self._runtime.build_prompt(self, timeline)
    raw = self._runtime.call_llm(messages)
    parsed = self._runtime.parse_response(raw)
    if not parsed.done:
        results = self._runtime.execute_tools(self, parsed.calls)
    ```
  - [x] Deprecate `codec` parameter (map to runtime internally with warning)

### Phase 2: Backward Compatibility

- [x] Create `dana/core/runtime/legacy.py` with `LegacyRuntime`:
  - [x] Wraps existing `PromptEngineer` and `ToolCaller` for `codec=None` case
  - [x] Allows gradual migration

- [x] Ensure old code still works:
  - [x] `STARAgent(agent_type="x", codec=CSXMLCodec)` → uses `AnthropicRuntime`
  - [x] `STARAgent(agent_type="x", codec=None)` → uses `LegacyRuntime`
  - [x] `STARAgent(agent_type="x")` → uses `AnthropicRuntime` (new default)

### Phase 3: Remove Local Disk Caching

- [x] Remove prompt template caching from runtime (was in LocalPromptAPI)
- [x] Prompts are built fresh each time
- [x] Learned context comes from Learner, not cached templates
- [x] Delete `.dana/dana_agent/*/prompts/system_prompt_template/` cache files in tests

## Files Implemented

| File | Status | Description |
|------|--------|-------------|
| `dana/core/runtime/__init__.py` | ✅ | AgentRuntime base class, ParsedResponse |
| `dana/core/runtime/anthropic.py` | ✅ | AnthropicRuntime implementation |
| `dana/core/runtime/legacy.py` | ✅ | LegacyRuntime for backward compat |
| `dana/core/agent/star_agent.py` | ✅ | Update to use runtime |
| `dana/core/runtime/tests/test_agent_runtime.py` | ✅ | Unit tests |

## Tests Required

Create `dana/core/runtime/tests/test_agent_runtime.py`:

- [x] `test_parsed_response_dataclass` - ParsedResponse has correct fields
- [x] `test_anthropic_runtime_initialization` - Creates with defaults
- [x] `test_anthropic_runtime_initialization_custom_llm` - Accepts injected LLM
- [x] `test_anthropic_runtime_build_prompt` - Returns list of LLMMessage
- [x] `test_anthropic_runtime_parse_response_done_true` - Parses done=true correctly
- [x] `test_anthropic_runtime_parse_response_done_false` - Parses done=false correctly
- [x] `test_anthropic_runtime_parse_response_with_tool_calls` - Extracts tool calls
- [x] `test_anthropic_runtime_execute_tools` - Executes and returns results
- [x] `test_star_agent_with_runtime_parameter` - Accepts runtime parameter
- [x] `test_star_agent_default_runtime` - Uses AnthropicRuntime by default
- [x] `test_star_agent_deprecated_codec_parameter` - codec still works with warning
- [x] `test_think_uses_runtime_methods` - _think() calls runtime.build_prompt, call_llm, etc.

Command to run tests:
```bash
pytest dana_agent/dana/core/runtime/tests/test_agent_runtime.py -v
```

Also run existing tests to ensure no regressions:
```bash
pytest dana_agent/tests/unit/test_agent.py -v
pytest dana_agent/tests/unit/test_tool_caller.py -v
pytest dana_agent/tests/unit/test_autonomy_in_template.py -v
```

## Success Criteria

1. `STARAgent(agent_type="x", runtime=AnthropicRuntime())` works
2. Default `STARAgent(agent_type="x")` uses `AnthropicRuntime`
3. Old `codec=CSXMLCodec` still works (emits deprecation warning)
4. `_think()` method uses runtime: build_prompt → call_llm → parse_response → execute_tools
5. All new tests pass
6. All existing tests pass (no regressions)
7. No references to "codec", "LocalPromptAPI", or "CodecToolCaller" in new runtime code

## Before Marking Complete

- [x] All tests pass (new and existing)
- [x] Uses structlog logger (not print)
- [x] Follows existing code patterns (check star_agent.py, tool_caller.py)
- [x] No unnecessary complexity (KISS)
- [x] No over-engineering (YAGNI)
- [x] Deprecation warning for `codec` parameter uses `warnings.warn`
- [x] ParsedResponse uses `@dataclass` decorator
- [x] AgentRuntime uses `ABC` and `@abstractmethod`

## When Complete

Run these commands to verify:
```bash
# Run new runtime tests
pytest dana_agent/dana/core/runtime/tests/test_agent_runtime.py -v

# Run existing agent tests (no regressions)
pytest dana_agent/tests/unit/test_agent.py -v
pytest dana_agent/tests/unit/test_tool_caller.py -v
pytest dana_agent/tests/unit/test_autonomy_in_template.py -v

# Run done-flag autonomy tests
pytest dana_agent/dana/core/agent/tests/test_done_flag_autonomy.py -v
```

Only if ALL tests pass, write this line to this file:

<promise>TASK COMPLETE</promise>

## References

- PRD: [agent-runtime-prd.md](./agent-runtime-prd.md)
- Related: [todo-driven-autonomy-ralph.md](./todo-driven-autonomy-ralph.md) (done-flag logic to preserve)
