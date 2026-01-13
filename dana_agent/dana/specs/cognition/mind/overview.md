# Mind Architecture

## Overview

The Mind is the agent's internal cognitive architecture - how it remembers, reflects, and constructs context.

```
                    ┌─────────────────────────────┐
                    │            Mind             │
                    │                             │
                    │  ┌────────────┐             │
                    │  │ Reflection │             │
                    │  └─────┬──────┘             │
                    │        ▼                    │
                    │  ┌──────────┐               │
                    │  │  Memory  │               │
                    │  └────┬─────┘               │
Data ───────────────┼───────▼─────────────────────┤
                    │  ┌───────────┐              │
                    │  │  Context  │              │
                    │  └─────┬─────┘              │
                    └────────┼────────────────────┘
                             ▼
                          ┌─────┐
                          │ LLM │
                          └─────┘
```

## Components

### Memory

Storage for the agent's experiences and knowledge.

| Type | Contents | Lifecycle |
|------|----------|-----------|
| stmemory | Live session timeline, working state | Session-scoped |
| ltmemory | Distilled episodes, patterns, knowledge | Persistent |

**Size is configurable** - stmemory can be small (direct inclusion) or large (needs RLM/vector access).

Spec: [memory-prd.md](./memory-prd.md)

### Reflection

Phases that process experiences into memory. Invoked at strategic moments.

| Phase | Purpose |
|-------|---------|
| Acquisitive | Identifying new information worth capturing |
| Episodic | Recording events and experiences |
| Integrative | Connecting patterns across episodes |
| Retentive | Selecting what to consolidate long-term |

**Distillation**: The process of running reflection phases to move insights from stmemory → ltmemory.

Spec: [reflection-prd.md](./reflection-prd.md)

### Context

The LLM's working window - constructed per-call from Memory and external Data.

**Context is constructed, not stored.** It's the assembly of what the agent presents to the LLM for a specific call.

Access pattern depends on source size:
- Small sources → direct inclusion
- Large sources → vector retrieval or RLM

Spec: [context-prd.md](./context-prd.md)

## Implementation Order

1. Context - how to construct LLM input from sources
2. Memory - stmemory/ltmemory storage and access
3. Reflection - distillation phases

## Specs

| Component | PRD | Implementation |
|-----------|-----|----------------|
| Context | [context-prd.md](./context-prd.md) | [context-ralph.md](./context-ralph.md) |
| Memory | [memory-prd.md](./memory-prd.md) | [memory-ralph.md](./memory-ralph.md) |
| Reflection | [reflection-prd.md](./reflection-prd.md) | [reflection-ralph.md](./reflection-ralph.md) |
