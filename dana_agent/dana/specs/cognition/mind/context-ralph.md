# Context - Implementation Spec

## Goal

Implement a Context builder that assembles LLM context from multiple sources (Data, Memory), automatically selecting access patterns based on source size.

## Demo

When complete, run `examples/agents/context/example.py`:

```python
from dana.core.context import ContextBuilder
from dana.common.resource import RLMResource

# Small source - direct inclusion
stmemory = "User asked about auth. Discussed login flow."

# Large source - RLM access
codebase = RLMResource(file="codebase.md")
codebase.load_file("all_source.txt")  # 500K tokens

# Build context
ctx = ContextBuilder(token_budget=50000)
ctx.add_source("stmemory", stmemory)
ctx.add_source("codebase", codebase)

context = ctx.build(task="Find security vulnerabilities in auth")

print(f"Tokens used: {context.tokens_used}")
print(f"Sources: {context.sources_used}")
print(context.text)
# → Contains stmemory (direct) + RLM answer from codebase
```

**What you'll see**: stmemory included verbatim (small), codebase queried via RLM with task-relevant answer extracted.

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
- [ ] Accept string sources (direct inclusion)
- [ ] Accept RLMResource sources (RLM access)
- [ ] Count tokens (use tiktoken or simple word estimate)
- [ ] Respect token budget
- [ ] Query RLM sources with task context
- [ ] Return assembled Context object

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
- [ ] Immutable dataclass
- [ ] Track which sources contributed
- [ ] Track token usage vs budget

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
- [ ] String sources wrap in simple adapter
- [ ] RLMResource already has query() method
- [ ] Adapter calls query(task) for RLM sources

## Current Progress

Check these files to see what exists:
- `dana_agent/dana/core/context/builder.py`
- `dana_agent/dana/core/context/context.py`
- `examples/agents/context/`

Update checkboxes above as you complete each requirement.

## Tests Required

Create `dana_agent/tests/unit/test_context_builder.py`:
- [ ] test_add_string_source - registers string source
- [ ] test_add_rlm_source - registers RLM source
- [ ] test_build_string_only - direct inclusion works
- [ ] test_build_respects_budget - truncates when over budget
- [ ] test_build_with_rlm - queries RLM source with task
- [ ] test_tokens_counted - tracks token usage
- [ ] test_sources_tracked - records which sources used

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_context_builder.py -v`

## Success Criteria

1. All tests pass
2. String sources included directly
3. RLM sources queried with task
4. Token budget respected
5. Example runs and shows mixed source types

## Before Marking Complete

- [ ] Review code for KISS/YAGNI compliance
- [ ] Simplify any overly complex implementations
- [ ] Remove unnecessary abstractions
- [ ] Ensure code is readable and maintainable

## When Complete

Output in this file:
<promise>CONTEXT BUILDER COMPLETE</promise>

## References

- PRD: [context-prd.md](./context-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [data-ralph.md](../data/data-ralph.md)
