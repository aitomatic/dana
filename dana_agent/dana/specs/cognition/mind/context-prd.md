# Context - Product Requirements Document

## Overview

Context is the LLM's working window - **constructed per-call** from available sources (Data and Memory). It's not stored; it's assembled fresh for each LLM invocation.

```
┌──────────┐     ┌──────────┐
│   Data   │     │  Memory  │
│(external)│     │(internal)│
└────┬─────┘     └────┬─────┘
     │                │
     └───────┬────────┘
             ▼
      ┌─────────────┐
      │   Context   │  ← assembled per-call
      │ (LLM window)│
      └──────┬──────┘
             ▼
          ┌─────┐
          │ LLM │
          └─────┘
```

## Problem Statement

Dana agents need to construct effective context for LLM calls by:
- Selecting relevant content from multiple sources
- Respecting token budget constraints
- Choosing appropriate access patterns (direct, vector, RLM) based on source size
- Prioritizing what to include when space is limited

Currently, context construction is ad-hoc and manual.

## Solution

Implement a Context builder that:
1. Accepts references to sources (Data, Memory)
2. Determines access pattern per source based on size
3. Extracts/retrieves relevant content
4. Assembles into a coherent context within token budget

## User Stories

1. **As an agent developer**, I want to declare what sources are available so the context builder can pull from them automatically.

2. **As an agent**, I want my context to include relevant memory and data without manually managing token budgets.

3. **As a system**, I want to use the cheapest access pattern (direct > vector > RLM) based on source size.

## Use Cases

| Scenario | Sources | Context Strategy |
|----------|---------|------------------|
| Simple chat | stmemory only | Direct inclusion |
| Chat with history | stmemory + ltmemory | Direct + vector retrieval |
| Research task | stmemory + data | Direct + RLM query |
| Complex agent | stmemory + ltmemory + data | Mixed strategies |

## Requirements

### Functional
- Register sources (Data, stmemory, ltmemory)
- Determine access pattern based on source size vs token budget
- Extract content from small sources (direct)
- Retrieve from large sources (vector similarity or RLM)
- Assemble into structured context
- Track token usage

### Non-Functional
- Context assembly < 1s for direct sources
- Graceful degradation when budget exceeded (prioritize, truncate)
- Configurable token budget (default: model's limit minus response reserve)

## Success Metrics

1. **Efficiency**: Uses cheapest access pattern that fits
2. **Relevance**: Retrieved content addresses the current task
3. **Budget compliance**: Never exceeds token limit

## Scope

### In MVP
- Source registration (Data, stmemory)
- Size-based access pattern selection
- Direct inclusion for small sources
- RLM integration for large Data sources
- Basic token counting

### Out of MVP (Future)
- ltmemory integration (requires Memory implementation)
- Vector retrieval
- Smart prioritization / relevance ranking
- Caching of retrieved content

## Demo

When Context MVP is complete, we can demonstrate:

```python
from dana.core.context import ContextBuilder
from dana.common.resource import RLMResource

# Register sources
ctx = ContextBuilder(token_budget=100000)
ctx.add_source("stmemory", session.timeline)        # small, direct
ctx.add_source("codebase", RLMResource("code.md"))  # large, RLM

# Build context for a task
context = ctx.build(task="Find authentication bugs")
# → stmemory included directly
# → codebase queried via RLM, answer included

print(context.tokens_used)  # 45000
print(context.sources_used) # ['stmemory', 'codebase']
```

**Demo narrative**: "Declare your sources once. Context builder automatically chooses direct inclusion or RLM based on size, stays within budget."

## References

- Implementation spec: [context-ralph.md](./context-ralph.md)
- Parent: [mind overview](./overview.md)
- Related: [data PRD](../data/data-prd.md)
