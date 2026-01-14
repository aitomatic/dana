# Context - Implementation Spec

**Status: ✅ COMPLETE**

## Goal

Implement a Context builder that assembles LLM context from multiple sources (Data, Memory), automatically selecting access patterns based on source size.

## Demo

Run: `examples/cognition/context/smart_context_assembly.py`

### Without ContextBuilder (The Problem)

```python
# WITHOUT CONTEXTBUILDER: Manual, ad-hoc context assembly

def build_context_manually(timeline, ltmemory, codebase, task):
    context_parts = []

    # 1. Timeline - just dump it
    context_parts.append(timeline.to_text())  # 5K tokens

    # 2. LTMemory - ??? How do we query it? How much to include?
    # ❌ Can't just dump memories.md (might be huge)
    # ❌ No automatic relevance filtering
    memories = open("memories.md").read()
    context_parts.append(memories[:10000])  # Arbitrary truncation

    # 3. Codebase - definitely can't fit
    # ❌ 500K tokens, context is only 128K
    # ❌ Have to manually decide what's relevant
    codebase_text = open("codebase.txt").read()
    # Give up and skip it? Include random chunks?

    # 4. Token budget - manual counting
    # ❌ Easy to exceed limit
    # ❌ No prioritization strategy

    return "\n".join(context_parts)
    # Result: Unreliable, inconsistent, often over budget
```

### With ContextBuilder (The Solution)

```python
# WITH CONTEXTBUILDER: Smart, automatic context assembly

from dana.core.context import ContextBuilder
from dana.core.memory import LTMemory
from dana.common.resource import RLMResource

# Register your sources
ctx = ContextBuilder(token_budget=50000)
ctx.add_source("timeline", timeline.to_text())           # Small → direct
ctx.add_source("ltmemory", LTMemory("./memories/"))      # Large → RLM query
ctx.add_source("codebase", RLMResource("codebase.md"))   # Huge → RLM query

# Build context for the current task
context = ctx.build(task="Find security vulnerabilities in auth")

# ✅ Timeline included directly (fits budget)
# ✅ LTMemory queried: "What do I know about auth security?"
# ✅ Codebase queried: "What code handles auth?"
# ✅ Token budget respected automatically
# ✅ Only relevant information extracted

print(f"Tokens: {context.tokens_used}/{context.budget}")  # 42000/50000
print(f"Sources: {context.sources_used}")  # ['timeline', 'ltmemory', 'codebase']
```

### What You'll See

```
ContextBuilder assembling context for task: "Find auth vulnerabilities"

Source: timeline (2,500 tokens)
  → Direct inclusion (under budget)

Source: ltmemory (queried via RLM)
  → "Past sessions found token expiry bugs in auth module"

Source: codebase (queried via RLM)
  → "Auth handled by login(), verify_token() in src/auth/"

Final context: 42,000 / 50,000 tokens
Sources used: timeline, ltmemory, codebase
```

## MVP Requirements

### 1. ContextBuilder (`dana_agent/dana/core/context/builder.py`)

```python
class ContextBuilder:
    """Builds LLM context from multiple sources."""

    def __init__(self, token_budget: int = 100000):
        self.token_budget = token_budget
        self.sources: dict[str, Source] = {}

    def add_source(self, name: str, source: str | RLMResource) -> None:
        """Register a source. Type determines access pattern."""

    def build(self, task: str = "") -> Context:
        """
        Assemble context from registered sources.

        For each source:
        - If str and fits budget: include directly
        - If RLMResource: query with task, include answer

        Returns Context with text, tokens_used, sources_used.
        """
```

Requirements:
- [x] Accept string sources (direct inclusion)
- [x] Accept RLMResource sources (RLM access)
- [x] Count tokens (use tiktoken or simple word estimate)
- [x] Respect token budget
- [x] Query RLM sources with task context
- [x] Return assembled Context object

### 2. Context (`dana_agent/dana/core/context/context.py`)

```python
@dataclass
class Context:
    """Assembled context ready for LLM."""
    text: str
    tokens_used: int
    sources_used: list[str]
    budget: int
```

Requirements:
- [x] Immutable dataclass
- [x] Track which sources contributed
- [x] Track token usage vs budget

### 3. Source Protocol

```python
class Source(Protocol):
    """Protocol for context sources."""

    def get_content(self, task: str = "") -> str:
        """Return content for inclusion in context."""

    def estimate_tokens(self) -> int:
        """Estimate token count."""
```

Requirements:
- [x] String sources wrap in simple adapter
- [x] RLMResource already has query() method
- [x] Adapter calls query(task) for RLM sources

Note: Implemented using a simpler `Queryable` protocol that just requires `query(question: str) -> str`. This works with both RLMResource and LTMemory without unnecessary complexity.

## Example Files (`examples/cognition/context/`)

- `smart_context_assembly.py` - Full demo with mixed source types

## Files Implemented

- `dana_agent/dana/core/context/builder.py` ✅
- `dana_agent/dana/core/context/context.py` ✅
- `dana_agent/dana/core/context/__init__.py` ✅
- `examples/cognition/context/` ✅

## Tests Required

Create `dana_agent/tests/unit/test_context_builder.py`:
- [x] test_add_string_source - registers string source
- [x] test_add_rlm_source - registers RLM source
- [x] test_build_string_only - direct inclusion works
- [x] test_build_respects_budget - truncates when over budget
- [x] test_build_with_rlm - queries RLM source with task
- [x] test_tokens_counted - tracks token usage
- [x] test_sources_tracked - records which sources used

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_context_builder.py -v`

## Success Criteria

1. ✅ All tests pass (12/12)
2. ✅ String sources included directly
3. ✅ RLM sources queried with task
4. ✅ Token budget respected
5. ✅ Example runs and shows mixed source types

## Before Marking Complete

- [x] Review code for KISS/YAGNI compliance
- [x] Simplify any overly complex implementations
- [x] Remove unnecessary abstractions
- [x] Ensure code is readable and maintainable

## When Complete

**You MUST run tests before marking complete:**
```bash
cd dana_agent && uv run pytest tests/unit/test_context_builder.py -v
```

Only if ALL tests pass, output the completion tag:
`<promise>` + `TASK COMPLETE` + `</promise>`

## STARAgent Integration

### Current State
- ✅ ContextBuilder implemented
- ✅ Files exist: `dana_agent/dana/core/context/`
- ✅ PromptEngineer uses ContextBuilder for context assembly

### Integration Tasks

| Task | Status | Description |
|------|--------|-------------|
| Create ContextBuilder | ✅ Complete | Implement `dana.core.context.builder` |
| Create Context dataclass | ✅ Complete | Implement `dana.core.context.context` |
| Integrate with PromptEngineer | ✅ Complete | Use ContextBuilder in `build_llm_request()` |
| Support Timeline as source | ✅ Complete | Direct inclusion of Timeline entries (as string) |
| Support LTMemory as source | ✅ Complete | RLM query for relevant memories |
| Support RLMResource as source | ✅ Complete | RLM query for external data |

### Integration Code

```python
# In prompt_engineer.py (or new context integration)
from dana.core.context import ContextBuilder

class PromptEngineer:
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        # NEW: Use ContextBuilder
        ctx = ContextBuilder(token_budget=self._agent._max_context_tokens)

        # Add timeline (direct inclusion)
        ctx.add_source("timeline", timeline.to_text())

        # Add ltmemory if available (RLM query)
        if self._agent._ltmemory:
            ctx.add_source("ltmemory", self._agent._ltmemory)

        # Build context with current task
        context = ctx.build(task=self._extract_current_task(timeline))

        # Assemble LLM messages
        return [
            LLMMessage(role="system", content=self.system_prompt),
            LLMMessage(role="user", content=context.text)
        ]
```

### Files Created
- `dana_agent/dana/core/context/__init__.py` ✅
- `dana_agent/dana/core/context/builder.py` ✅
- `dana_agent/dana/core/context/context.py` ✅
- `dana_agent/tests/unit/test_context_builder.py` ✅
- `examples/cognition/context/smart_context_assembly.py` ✅

## References

- PRD: [context-prd.md](./context-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [data-ralph.md](../data/data-ralph.md)
