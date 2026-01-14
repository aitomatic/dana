# Data - Product Requirements Document

## Overview

Data refers to **external sources** the agent can access: files, books, APIs, corpora. Unlike Memory (internal), Data is external artifacts the agent reads but doesn't own.

| Aspect | Description |
|--------|-------------|
| Nature | External artifacts |
| Source | Files, books, APIs, corpora |
| Mutability | Static (read-only from agent's perspective) |
| Examples | Codebases, logs, documentation, papers |

## Problem Statement

Dana agents are limited by LLM context windows. When working with large external sources (codebases, log files, documentation), agents must either:
- Manually chunk and summarize before querying
- Accept degraded accuracy from truncation
- Use expensive models with larger contexts

## Solution

Implement RLM (Recursive Language Model) pattern: the LLM writes Python code to programmatically explore large sources instead of extracting everything into context.

**RLM returns answers, not content** - the source stays external, only the result enters context.

```
┌────────────────┐
│  Large Source  │  (500K+ tokens)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   RLM Loop     │  LLM writes Python to explore
│  (max 20 iter) │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Answer      │  (small, fits in context)
└────────────────┘
```

## User Stories

1. **As a developer**, I want to query a large codebase so I can find patterns and understand architecture without manual searching.

2. **As an ops engineer**, I want to analyze large log files so I can identify issues without truncating.

3. **As a researcher**, I want to query document collections so I can extract insights from corpora that don't fit in context.

## Use Cases

| Use Case | Input Size | Example Query |
|----------|------------|---------------|
| Codebase Q&A | 500K+ tokens | "What functions handle authentication?" |
| Log analysis | 1M+ tokens | "Find all errors related to database timeouts" |
| Document search | 500K+ tokens | "Summarize all sections mentioning compliance" |

## Requirements

### Functional
- Query large external sources using natural language
- LLM writes Python to explore source programmatically
- Sub-LLM calls for semantic tasks (summarize, extract)
- Load files into sources

### Non-Functional
- Max 20 iterations per query (bounded compute)
- Output truncated to 10KB (bounded response size)
- Safe execution (no file writes, no shell access)

## Success Metrics

1. **Correctness**: Queries return accurate answers for sources > 100K tokens
2. **Efficiency**: Average query completes in < 10 iterations
3. **Safety**: No sandbox escapes in adversarial testing

## Scope

### In MVP
- RLM access pattern for external data sources
- Single-file source
- Python-based exploration
- Basic load operations

### Out of MVP (Future)
- Multi-file sources with indexing
- Streaming responses
- Caching of intermediate results

## STARAgent Integration

### Current State
- ✅ `RLMResource` is available as a tool that agents can use
- ✅ Agents can attach RLMResource via `agent.with_resources(RLMResource(...))`
- ❌ ContextBuilder (not yet implemented) should query RLMResource automatically

### Integration Requirements

1. **As Agent Tool** (Current - Working)
   ```python
   agent = STARAgent(...)
   agent.with_resources(RLMResource(file="codebase.md"))
   # Agent can call query(), append(), load_file() as tools
   ```

2. **As Context Source** (Future - Requires ContextBuilder)
   ```python
   # ContextBuilder should accept RLMResource as a data source
   ctx = ContextBuilder(token_budget=50000)
   ctx.add_source("codebase", RLMResource(file="codebase.md"))

   # When building context, RLMResource is queried with task
   context = ctx.build(task="Find auth bugs")
   ```

3. **For LTMemory Queries** (Current - Working)
   - LTMemory internally uses RLMResource for querying large memory stores
   - This is transparent to STARAgent

## Risks

| Risk | Mitigation |
|------|------------|
| LLM writes inefficient code | Strategies in system prompt |
| Infinite loops in generated code | Execution timeout per iteration |
| Sandbox escape | Restricted builtins, no dangerous modules |

## Demo

When Data MVP is complete, we can demonstrate:

```python
from dana.common.resource import RLMResource

# Load a massive codebase dump (500K+ tokens)
data = RLMResource(file="huge_codebase.md")
data.load_file("all_source_files.txt")

# Query it - LLM writes Python to search, not stuffing context
answer = data.query("What functions handle authentication?")
# → Returns: "Authentication is handled by login(), verify_token(),
#    and refresh_session() in src/auth/handlers.py..."

answer = data.query("Find all TODO comments and categorize them")
# → Returns: "Found 47 TODOs: 23 are bug fixes, 15 are features,
#    9 are refactoring tasks..."
```

**Demo narrative**: "Ask questions about documents 10x larger than the context window. Watch the agent write Python to explore instead of cramming everything in."

## References

- Implementation spec: [data-ralph.md](./data-ralph.md)
- Parent: [cognition overview](../overview.md)
