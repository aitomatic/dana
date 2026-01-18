# AgentRuntime Refactor - Implementation Spec

**Status: ⚠️ IN PROGRESS**

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

- [ ] Create `dana/core/runtime/__init__.py` with:
  - [ ] `ParsedResponse` dataclass with fields: `done`, `reasoning`, `response`, `tool_calls`
  - [ ] `AgentRuntime` abstract base class with methods:
    - [ ] `build_prompt(agent, timeline, learned_context=None) -> list[LLMMessage]`
    - [ ] `call_llm(messages) -> str`
    - [ ] `parse_response(raw) -> ParsedResponse`
    - [ ] `execute_tools(agent, tool_calls) -> list[dict]`
    - [ ] `get_output_instructions() -> str`

- [ ] Create `dana/core/runtime/anthropic.py` with `AnthropicRuntime`:
  - [ ] `__init__(model, temperature, max_tokens, llm=None)` - owns LLM instance
  - [ ] Migrate prompt building from `LocalPromptAPI`
  - [ ] Migrate LLM calling (currently in star_agent._think)
  - [ ] Migrate response parsing from `CodecToolCaller.parse_llm_response`
  - [ ] Migrate tool execution from `CodecToolCaller.execute_tool_calls`
  - [ ] Include done-flag validation logic

- [ ] Update `dana/core/agent/star_agent.py`:
  - [ ] Add `runtime` parameter to `__init__`
  - [ ] Default to `AnthropicRuntime()` when no runtime provided
  - [ ] Store as `self._runtime`
  - [ ] Update `_think()` to use runtime methods:
    ```python
    messages = self._runtime.build_prompt(self, timeline)
    raw = self._runtime.call_llm(messages)
    parsed = self._runtime.parse_response(raw)
    if not parsed.done:
        results = self._runtime.execute_tools(self, parsed.calls)
    ```
  - [ ] Deprecate `codec` parameter (map to runtime internally with warning)

### Phase 2: Backward Compatibility

- [ ] Create `dana/core/runtime/legacy.py` with `LegacyRuntime`:
  - [ ] Wraps existing `PromptEngineer` and `ToolCaller` for `codec=None` case
  - [ ] Allows gradual migration

- [ ] Ensure old code still works:
  - [ ] `STARAgent(agent_type="x", codec=CSXMLCodec)` → uses `AnthropicRuntime`
  - [ ] `STARAgent(agent_type="x", codec=None)` → uses `LegacyRuntime`
  - [ ] `STARAgent(agent_type="x")` → uses `AnthropicRuntime` (new default)

### Phase 3: Remove Local Disk Caching

- [ ] Remove prompt template caching from runtime (was in LocalPromptAPI)
- [ ] Prompts are built fresh each time
- [ ] Learned context comes from Learner, not cached templates
- [ ] Delete `.dana/dana_agent/*/prompts/system_prompt_template/` cache files in tests

## Files Implemented

| File | Status | Description |
|------|--------|-------------|
| `dana/core/runtime/__init__.py` | ❌ | AgentRuntime base class, ParsedResponse |
| `dana/core/runtime/anthropic.py` | ❌ | AnthropicRuntime implementation |
| `dana/core/runtime/legacy.py` | ❌ | LegacyRuntime for backward compat |
| `dana/core/agent/star_agent.py` | ❌ | Update to use runtime |
| `dana/core/runtime/tests/test_agent_runtime.py` | ❌ | Unit tests |

## Tests Required

Create `dana/core/runtime/tests/test_agent_runtime.py`:

- [ ] `test_parsed_response_dataclass` - ParsedResponse has correct fields
- [ ] `test_anthropic_runtime_initialization` - Creates with defaults
- [ ] `test_anthropic_runtime_initialization_custom_llm` - Accepts injected LLM
- [ ] `test_anthropic_runtime_build_prompt` - Returns list of LLMMessage
- [ ] `test_anthropic_runtime_parse_response_done_true` - Parses done=true correctly
- [ ] `test_anthropic_runtime_parse_response_done_false` - Parses done=false correctly
- [ ] `test_anthropic_runtime_parse_response_with_tool_calls` - Extracts tool calls
- [ ] `test_anthropic_runtime_execute_tools` - Executes and returns results
- [ ] `test_star_agent_with_runtime_parameter` - Accepts runtime parameter
- [ ] `test_star_agent_default_runtime` - Uses AnthropicRuntime by default
- [ ] `test_star_agent_deprecated_codec_parameter` - codec still works with warning
- [ ] `test_think_uses_runtime_methods` - _think() calls runtime.build_prompt, call_llm, etc.

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

- [ ] All tests pass (new and existing)
- [ ] Uses structlog logger (not print)
- [ ] Follows existing code patterns (check star_agent.py, tool_caller.py)
- [ ] No unnecessary complexity (KISS)
- [ ] No over-engineering (YAGNI)
- [ ] Deprecation warning for `codec` parameter uses `warnings.warn`
- [ ] ParsedResponse uses `@dataclass` decorator
- [ ] AgentRuntime uses `ABC` and `@abstractmethod`

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
