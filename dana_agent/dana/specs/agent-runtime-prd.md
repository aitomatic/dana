# AgentRuntime Refactor PRD

**Status: DRAFT**

## Goal

Replace the confusing `codec`, `LocalPromptAPI`, `CodecToolCaller`, and `PromptEngineer` abstractions with a single, intuitive concept: **AgentRuntime**.

An AgentRuntime is a complete, packaged configuration for a target platform (Anthropic, OpenAI, NVIDIA Thor, etc.). It encapsulates all platform-specific behavior for how the agent runs.

## Problem

Current naming is confusing for library users and developers:

| Current Name | What It Actually Does | Problem |
|--------------|----------------------|---------|
| `codec` | Defines output format + parsing | Jargon, not intuitive |
| `LocalPromptAPI` | Builds prompts, LLM requests, caches | "Local"? "API"? |
| `CodecToolCaller` | Parses responses + executes tools | Does two things, name suggests only one |
| `PromptEngineer` | Legacy XML-based prompts | Confusing with `LocalPromptAPI` |
| `self._prompt_engineer` | Holds either `LocalPromptAPI` or `PromptEngineer` | Same variable, different types |

## Solution

### The AgentRuntime Abstraction

An **AgentRuntime** is the deployment target configuration. It owns all platform-specific behavior:

```python
class AnthropicRuntime:
    """Runtime for Anthropic platform"""

    def build_prompt(self, agent, timeline) -> list[Message]:
        """Build LLM messages for this platform"""

    def call_llm(self, messages) -> str:
        """Call the LLM on this platform"""

    def parse_response(self, raw: str) -> ParsedResponse:
        """Parse LLM response for this platform"""

    def execute_tools(self, agent, calls) -> list[Result]:
        """Execute tool calls"""
```

### Clean Agent Code

The agent orchestrates the STAR loop, delegating all platform details to the runtime:

```python
class STARAgent:
    def __init__(self, agent_type: str, runtime: AgentRuntime = None):
        self._runtime = runtime or AnthropicRuntime()  # Default

    def _think(self, trace_percepts):
        messages = self._runtime.build_prompt(self, timeline)
        raw = self._runtime.call_llm(messages)
        parsed = self._runtime.parse_response(raw)
        if not parsed.done:
            results = self._runtime.execute_tools(self, parsed.calls)
        # ... loop logic
```

### Prepackaged Runtimes

```python
# LLM API providers
class AnthropicRuntime(AgentRuntime): ...    # XML-based, prompt caching
class OpenAIRuntime(AgentRuntime): ...       # Native function calling, JSON mode

# Local/edge platforms
class OllamaRuntime(AgentRuntime): ...       # Local models, simpler prompts
class ThorRuntime(AgentRuntime): ...         # NVIDIA Thor for automotive/robotics

# Cloud platforms
class BedrockRuntime(AgentRuntime): ...      # AWS Bedrock
class AzureRuntime(AgentRuntime): ...        # Azure OpenAI
class VertexRuntime(AgentRuntime): ...       # Google Vertex AI
```

### User Mental Model

```
┌─────────────────────────────────────┐
│              Agent                  │
│                                     │
│  "What the agent does"              │
│  - Identity                         │
│  - Tools (resources, workflows)     │
│                                     │
│  runtime = AnthropicRuntime()           │
│  "How it talks to the platform"     │
└─────────────────────────────────────┘
```

Users think about:
1. **What** the agent does (identity, tools)
2. **Where** it runs (runtime)

Everything else is invisible plumbing.

## Design Details

### AgentRuntime Base Class

```python
@dataclass
class ParsedResponse:
    done: bool
    reasoning: str | None
    response: str | None
    tool_calls: list[dict]

class AgentRuntime(ABC):
    """Base class for platform runtimes"""

    @abstractmethod
    def build_prompt(self, agent: "STARAgent", timeline: Timeline) -> list[LLMMessage]:
        """Build LLM messages including system prompt, context, user message"""

    @abstractmethod
    def call_llm(self, messages: list[LLMMessage]) -> str:
        """Call the LLM and return raw response"""

    @abstractmethod
    def parse_response(self, raw: str) -> ParsedResponse:
        """Parse raw LLM response into structured data"""

    @abstractmethod
    def execute_tools(self, agent: "STARAgent", tool_calls: list[dict]) -> list[dict]:
        """Execute tool calls and return results"""

    def get_output_instructions(self) -> str:
        """Return format instructions for the system prompt"""
```

### AnthropicRuntime Implementation

```python
class AnthropicRuntime(AgentRuntime):
    """Runtime for Anthropic Claude models"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0,
        max_tokens: int = 8192,
    ):
        self._llm = LLM(provider="anthropic", model=model)
        self._temperature = temperature
        self._max_tokens = max_tokens

    def get_output_instructions(self) -> str:
        return """
## STRICT OUTPUT FORMAT

Every response MUST follow this exact XML structure:

<done>false</done>
<function_call>
<invoke name="tool:method">
<parameter name="param">value</parameter>
</invoke>
</function_call>
<response></response>

OR

<done>true</done>
<function_call></function_call>
<response>Final answer with actual data</response>

## CRITICAL RULES

1. <done> is ALWAYS required - must be literal `true` or `false`
2. done=false requires non-empty <function_call>
3. done=true requires non-empty <response>
"""

    def build_prompt(self, agent, timeline) -> list[LLMMessage]:
        # Build system prompt with identity, tools, output instructions
        # Build context from timeline
        # Build user message
        ...

    def call_llm(self, messages) -> str:
        response = self._llm.chat_response_sync(
            messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response

    def parse_response(self, raw: str) -> ParsedResponse:
        # Extract <done>, <function_call>, <response>, <thinking>
        done = self._extract_done(raw)
        tool_calls = self._extract_tool_calls(raw)
        response = self._extract_response(raw)
        reasoning = self._extract_thinking(raw)
        return ParsedResponse(done=done, reasoning=reasoning, response=response, tool_calls=tool_calls)

    def execute_tools(self, agent, tool_calls) -> list[dict]:
        # Find resources/agents/workflows and invoke methods
        ...
```

### Migration Path

| Old | New |
|-----|-----|
| `codec=CSXMLCodec` | `runtime=AnthropicRuntime()` |
| `codec=None` | `runtime=LegacyRuntime()` (deprecated) |
| `self._prompt_engineer` | `self._runtime` |
| `self._tool_caller` | `self._runtime` |
| `LocalPromptAPI` | Absorbed into runtime classes |
| `CodecToolCaller` | Absorbed into runtime classes |
| `PromptEngineer` | `LegacyRuntime` (deprecated) |

## MVP Requirements

### Phase 1: Core AgentRuntime Abstraction

- [ ] Create `AgentRuntime` base class with abstract methods
- [ ] Create `ParsedResponse` dataclass
- [ ] Implement `AnthropicRuntime` (migrate from `CSXMLCodec` + `LocalPromptAPI` + `CodecToolCaller`)
- [ ] Update `STARAgent.__init__` to accept `runtime` parameter
- [ ] Update `STARAgent._think()` to use runtime methods
- [ ] Update `STARAgent._act()` to use runtime methods
- [ ] Deprecate `codec` parameter (still works, maps to runtime internally)

### Phase 2: Additional Runtimes

- [ ] Implement `OpenAIRuntime` with native function calling
- [ ] Implement `OllamaRuntime` for local models
- [ ] Implement `LegacyRuntime` for backward compatibility with `codec=None`

### Phase 3: Cleanup

- [ ] Remove `LocalPromptAPI` (absorbed into runtimes)
- [ ] Remove `CodecToolCaller` (absorbed into runtimes)
- [ ] Deprecate `PromptEngineer` (replaced by `LegacyRuntime`)
- [ ] Update all tests
- [ ] Update documentation

## File Changes

| File | Change |
|------|--------|
| `dana/core/runtime/__init__.py` | NEW: AgentRuntime base class, ParsedResponse |
| `dana/core/runtime/anthropic.py` | NEW: AnthropicRuntime implementation |
| `dana/core/runtime/openai.py` | NEW: OpenAIRuntime implementation |
| `dana/core/runtime/ollama.py` | NEW: OllamaRuntime implementation |
| `dana/core/runtime/legacy.py` | NEW: LegacyRuntime for backward compat |
| `dana/core/agent/star_agent.py` | UPDATE: Use runtime instead of codec/prompt_engineer/tool_caller |
| `dana/core/agent/components/tool_caller.py` | DEPRECATE: Functionality moves to runtimes |
| `dana/core/knowledge/prompts/prompt_api.py` | DEPRECATE: Functionality moves to runtimes |
| `dana/core/knowledge/prompts/codecs.py` | DEPRECATE: Replaced by runtimes |

## Success Criteria

1. `STARAgent(agent_type="x", runtime=AnthropicRuntime())` works
2. Default `STARAgent(agent_type="x")` uses `AnthropicRuntime`
3. Old `codec=CSXMLCodec` still works (deprecated warning)
4. All existing tests pass
5. `_think()` method reads as clear flow: build_prompt → call_llm → parse_response → execute_tools
6. No references to "codec", "LocalPromptAPI", "CodecToolCaller" in new code

## Separation of Concerns: AgentRuntime vs Learner

### What the AgentRuntime Does (Platform Communication)

The AgentRuntime handles all **platform-specific** behavior:
- Build prompts in the format this platform expects
- Call the LLM using this platform's API
- Parse responses in this platform's format
- Execute tools

The AgentRuntime does **NOT** persist prompts. It builds them fresh each time.

### What the Learner Does (Learning & Persistence)

The Learner handles all **learning and persistence** via the existing Reflect phase:
- Analyzes what happened (prompt used, actions taken, outcomes)
- Evolves the prompt based on learnings
- Persists the evolved prompt for future sessions
- Provides learned context to the AgentRuntime for prompt building

### Why This Separation?

1. **Learning is orthogonal to platform** - An agent can learn on Anthropic, deploy on Thor
2. **Clear responsibilities** - AgentRuntime = "how to talk", Learner = "what to remember"
3. **Existing infrastructure** - Learner already has 4-phase reflection with persistence:
   - ACQUISITIVE: Immediate learning, stores `_acquisitive_learning_markdown`
   - EPISODIC: Episode-level reflection
   - INTEGRATIVE: Multi-episode integration
   - RETENTIVE: Long-term maintenance

### Flow with Learning

```python
class STARAgent:
    def _think(self, trace_percepts):
        # Learner provides learned context (if any)
        learned_context = self._learner.get_learned_context() if self._learner else {}

        # AgentRuntime builds prompt with learned context
        messages = self._runtime.build_prompt(self, timeline, learned_context)
        raw = self._runtime.call_llm(messages)
        parsed = self._runtime.parse_response(raw)

        # Track what was used for reflection
        trace_percepts["prompt_used"] = messages
        ...

    def _reflect(self, trace_outputs):
        # Learner analyzes and may evolve prompt
        if self._learner:
            self._learner._reflect_acquisitive(trace_outputs)  # Existing mechanism
```

### Prompt Persistence via Learner

The Learner already persists learnings via `_store_acquisitive_learning_markdown()`.
Prompt evolution can use the same mechanism:

```python
class Learner:
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        # Existing: analyze what happened
        context = self._build_analysis_context(trace_acquisitive, timeline_context)
        llm_markdown = self._call_llm_for_analysis(context, ...)

        # Existing: persist learnings
        self._store_acquisitive_learning_markdown(llm_markdown)

        # Could add: persist evolved prompt if needed
        # self._store_evolved_prompt(evolved_prompt)
```

### What About LocalPromptAPI's Disk Caching?

The current `LocalPromptAPI` caches rendered prompts to `.dana/.../v1.prompt` files.
This is **removed** because:

1. It causes bugs (stale cached prompts don't reflect code changes)
2. It conflates caching (performance) with learning (behavior evolution)
3. The performance benefit is negligible (just string interpolation)
4. If prompt persistence is needed, it should go through the Learner

**Note:** This is separate from Anthropic's server-side prompt caching (`cache_control`),
which is a platform feature the AgentRuntime can use for cost/latency benefits.

## Design Decisions

1. **AgentRuntime owns the LLM instance** by default, but allows injection for testing:
   ```python
   class AnthropicRuntime:
       def __init__(self, model="claude-sonnet-4-20250514", llm=None):
           self._llm = llm or LLM(provider="anthropic", model=model)
   ```

2. **Runtime-specific configuration** via each runtime's `__init__` parameters:
   ```python
   AnthropicRuntime(model="claude-sonnet-4-20250514", prompt_caching=True)
   OpenAIRuntime(model="gpt-4o", use_native_tools=True)
   ThorRuntime(endpoint="...", safety_level="automotive")
   ```

3. **No local disk caching of prompts in AgentRuntime** - removed to avoid stale prompt bugs

4. **Prompt persistence via Learner** - uses existing Reflect phase infrastructure

## Non-Goals

- Changing STAR loop logic (See-Think-Act-Reflect)
- Changing tool/resource/workflow APIs
- Changing Timeline or state management
- Changing Learner internals (just clarifying its role in prompt persistence)
- Performance optimization (same perf as before)
