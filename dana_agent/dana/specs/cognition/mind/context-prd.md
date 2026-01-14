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

## STARAgent Integration

### Current State
- ✅ ContextBuilder implemented and integrated
- ✅ STARAgent's `PromptEngineer.build_llm_request()` uses ContextBuilder
- ✅ Unified context assembly from Timeline, LTMemory, and RLMResources

### Integration Status

ContextBuilder is integrated in `PromptEngineer`:

```python
# In PromptEngineer.build_llm_request()
ctx = ContextBuilder(token_budget=timeline.max_context_tokens)

# Timeline included as direct source
if context_messages:
    timeline_lines = ["<TIMELINE>"]
    for msg in context_messages:
        timeline_lines.append(f"<ENTRY>{msg.content}</ENTRY>")
    timeline_lines.append("</TIMELINE>")
    ctx.add_source("timeline", "\n".join(timeline_lines))

# LTMemory added if available (RLM query)
ltmemory = getattr(self._agent, "_ltmemory", None)
if ltmemory is not None:
    ctx.add_source("ltmemory", _TaggedQueryable(ltmemory, "LTMEMORY"))

# RLMResources automatically registered
for resource in self._agent._resources:
    if hasattr(resource, "query") and hasattr(resource, "resource_id"):
        ctx.add_source(resource.resource_id, _TaggedQueryable(resource, resource.resource_id.upper()))

context = ctx.build(task=task)
# Context assembled and included in LLM messages
```

### Integration Requirements

1. **Replace ad-hoc assembly in PromptEngineer**
   - ContextBuilder becomes the standard way to assemble context
   - PromptEngineer uses ContextBuilder internally

2. **Support all source types**
   - Timeline/STMemory (direct inclusion)
   - LTMemory (RLM query for relevant past knowledge)
   - RLMResource (RLM query for external data)

3. **Token budget management**
   - ContextBuilder tracks and respects token limits
   - Prioritizes sources based on relevance and size

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
