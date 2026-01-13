# Cognition Architecture

## Overview

The cognitive architecture defines how Dana agents process information from external and internal sources to construct context for LLM calls.

```
┌──────────────────────────────────────────────────────────────────┐
│                          COGNITION                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐              ┌─────────────────────────────────┐  │
│   │   Data   │              │             Mind                │  │
│   │(external)│              │                                 │  │
│   │          │              │  ┌────────────┐                 │  │
│   │ Files    │              │  │ Reflection │                 │  │
│   │ Books    │              │  └─────┬──────┘                 │  │
│   │ APIs     │              │        │ (distillation)         │  │
│   │ Corpora  │              │        ▼                        │  │
│   │          │              │  ┌──────────────────────┐       │  │
│   │          │              │  │       Memory         │       │  │
│   │          │              │  │  ┌────────┬────────┐ │       │  │
│   │          │              │  │  │stmemory│ltmemory│ │       │  │
│   │          │              │  │  └────────┴────────┘ │       │  │
│   │          │              │  └──────────┬───────────┘       │  │
│   └────┬─────┘              │             │                   │  │
│        │                    └─────────────┼───────────────────┘  │
│        │                                  │                      │
│        └─────────────┬────────────────────┘                      │
│                      ▼                                           │
│               ┌───────────┐                                      │
│               │  Context  │  ← assembled per-call                │
│               └─────┬─────┘                                      │
│                     ▼                                            │
│                  ┌─────┐                                         │
│                  │ LLM │                                         │
│                  └─────┘                                         │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### Data (External)

External sources the agent can access but doesn't own.

| Aspect | Description |
|--------|-------------|
| Nature | External artifacts (read-only) |
| Examples | Files, books, APIs, codebases, logs, corpora |
| Access | RLM (LLM writes Python to explore large sources) |
| Scope | [data/](./data/) |

### Mind (Internal)

The agent's internal cognitive architecture.

| Component | Purpose |
|-----------|---------|
| **Memory** | Storage for experiences and knowledge |
| - stmemory | Session timeline, working state (configurable size) |
| - ltmemory | Persistent distilled knowledge |
| **Reflection** | Process that transforms experiences into memory |
| - Acquisitive | What's new/worth capturing? |
| - Episodic | What happened? |
| - Integrative | How does it connect? |
| - Retentive | What to keep? |
| **Context** | Assembled LLM window from sources |

Scope: [mind/](./mind/)

## Information Flow

```
Experience
    │
    ▼
stmemory (accumulates during session)
    │
    ▼ [Reflection triggered]
    │
    ├─→ Acquisitive → candidates
    ├─→ Episodic → narrative
    ├─→ Integrative → connections (queries ltmemory)
    └─→ Retentive → final memories
                        │
                        ▼
                    ltmemory (persistent)
```

```
[LLM call needed]
    │
    ▼
Context Builder
    │
    ├─→ stmemory (direct if small, RLM if large)
    ├─→ ltmemory (vector or RLM)
    └─→ Data (RLM)
            │
            ▼
        Context (assembled)
            │
            ▼
          LLM
```

## Design Principles

1. **Context is constructed, not stored** - assembled fresh per-call from sources
2. **Access pattern depends on size** - direct if small, vector/RLM if large
3. **Reflection feeds Memory** - experiences are processed, not just dumped
4. **Data is external to Mind** - agent accesses data but doesn't own it
5. **RLM returns answers, not content** - keeps context lean

## Specs

### Data
| Document | Purpose |
|----------|---------|
| [data-prd.md](./data/data-prd.md) | What & why |
| [data-ralph.md](./data/data-ralph.md) | Implementation spec |

### Mind
| Component | PRD | Implementation |
|-----------|-----|----------------|
| Context | [context-prd.md](./mind/context-prd.md) | [context-ralph.md](./mind/context-ralph.md) |
| Memory | [memory-prd.md](./mind/memory-prd.md) | [memory-ralph.md](./mind/memory-ralph.md) |
| Reflection | [reflection-prd.md](./mind/reflection-prd.md) | [reflection-ralph.md](./mind/reflection-ralph.md) |

## Implementation Order

| Order | Component | Depends On | Promise |
|-------|-----------|------------|---------|
| 1 | Data | - | `DATA ACCESS COMPLETE` |
| 2 | Memory | Data (ltmemory uses RLM) | `MEMORY COMPLETE` |
| 3 | Context | Data, Memory | `CONTEXT BUILDER COMPLETE` |
| 4 | Reflection | Memory | `REFLECTION COMPLETE` |

## Demo (Full System)

When all components are complete:

```python
from dana.core.memory import STMemory, LTMemory
from dana.core.context import ContextBuilder
from dana.core.reflection import Reflection
from dana.common.resource import RLMResource

# === Session setup ===
stmem = STMemory(max_entries=100)
ltmem = LTMemory(path="./memories/")
codebase = RLMResource(file="codebase.md")

# === During session ===
stmem.append("user", "Find auth bugs")
stmem.append("agent", "Searching...")
# ... more interactions ...

# === Build context for LLM call ===
ctx = ContextBuilder(token_budget=50000)
ctx.add_source("stmemory", stmem)
ctx.add_source("ltmemory", ltmem)
ctx.add_source("codebase", codebase)

context = ctx.build(task="Find authentication vulnerabilities")
# → Assembles from all sources, respects budget

# === End of session: reflect ===
reflection = Reflection()
result = reflection.run(stmemory=stmem, ltmemory=ltmem)
# → Distills session into durable memories

# === Next session ===
# ltmemory now contains lessons from previous session
# Agent can recall: "Last time, auth bugs were in token validation..."
```

**Demo narrative**: "Agent with memory that persists, learns from experience, and efficiently queries large external data."
