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

| Order | Component | Depends On | Status | Promise |
|-------|-----------|------------|--------|---------|
| 1 | Data | - | ✅ Complete | `DATA ACCESS COMPLETE` |
| 2 | Memory | Data (ltmemory uses RLM) | ✅ Complete | `MEMORY COMPLETE` |
| 3 | Context | Data, Memory | ✅ Complete | `CONTEXT BUILDER COMPLETE` |
| 4 | Reflection | Memory | ✅ Complete | `REFLECTION COMPLETE` |
| 5 | STARAgent Integration | All above | ✅ Complete | `STARAGENT COGNITION COMPLETE` |

## STARAgent Integration

The cognition architecture must be integrated into STARAgent to provide agents with memory, reflection, and intelligent context construction.

### Codec System Architecture

STARAgent supports two modes based on whether a codec is provided:

| Mode | Components | Status |
|------|------------|--------|
| **With codec** (recommended) | `LocalPromptAPI` + `CodecToolCaller` + `CSXMLCodec` | ✅ Primary path |
| **Without codec** (legacy) | `PromptEngineer` + `ToolCaller` | ⚠️ Backward compatibility only |

**The codec system is the preferred approach.** It provides structured LLM communication via `CSXMLCodec`, which defines both the format instructions for the LLM and the parsing logic for responses.

### Current STARAgent State

| STARAgent Component | Cognition Equivalent | Integration Status |
|---------------------|---------------------|-------------------|
| `Timeline` | STMemory | ⚠️ Parallel implementations - both serve different purposes |
| `Learner` | Reflection | ✅ Integrated - persists to LTMemory in RETENTIVE phase |
| `LocalPromptAPI` | ContextBuilder | ✅ Integrated - uses ContextBuilder for context assembly (with codec) |
| `_ltmemory` | LTMemory | ✅ Integrated - initialized via `ltmemory_path` parameter |

### Integration Requirements

1. **Memory Integration**
   - STARAgent should accept optional `STMemory` and `LTMemory` in constructor
   - Timeline can wrap or replace STMemory (they serve similar purposes)
   - LTMemory should be queryable during context building

2. **Context Integration (Codec System)**
   - `LocalPromptAPI.build_llm_request()` uses ContextBuilder internally
   - ContextBuilder assembles from: Timeline/STMemory, LTMemory, registered Data sources
   - Codec provides format instructions via `codec.get_instruction()`
   - Tools are formatted via `codec.construct()` for each tool signature

3. **Reflection Integration**
   - `Learner` should use `Reflection` for the distillation pipeline
   - Retentive phase must persist to LTMemory
   - Reflection should be triggered at session end or explicit request

### Integration Points in STARAgent

```python
from dana.core.knowledge.prompts.codecs import CSXMLCodec

class STARAgent:
    def __init__(
        self,
        ...,
        codec=CSXMLCodec,  # Enable codec system (recommended)
        ltmemory_path: str | None = None
    ):
        # Existing
        self._timeline = Timeline(...)
        self._learner = learner
        self._codec = codec

        # NEW: Add LTMemory
        self._ltmemory = LTMemory(path=ltmemory_path) if ltmemory_path else None

        # Codec-aware prompt and tool handling
        if codec is not None:
            # NEW SYSTEM (recommended)
            self._prompt_engineer = LocalPromptAPI(self, codec=codec, ...)
            self._tool_caller = CodecToolCaller(self, codec=codec)
        else:
            # LEGACY SYSTEM (backward compatibility)
            self._prompt_engineer = PromptEngineer(self)
            self._tool_caller = ToolCaller(self)

    def _think(self, trace_percepts):
        # LocalPromptAPI uses ContextBuilder internally
        # Codec formats tool instructions and parses responses
        context = self._prompt_engineer.build_llm_request(self._timeline)

    def _reflect(self, trace_outputs):
        # Learner should persist to LTMemory
        if self._ltmemory and self._learner:
            reflection = Reflection()
            result = reflection.run(
                stmemory=self._timeline,
                ltmemory=self._ltmemory
            )
```

## Demo (Full System)

Run: `examples/cognition/full_system/cognitive_agent.py`

### Without Cognition Architecture (The Problem)

```python
# WITHOUT COGNITION: Agent is stateless, context-limited, forgetful

class BasicAgent:
    def run(self, task):
        # Problem 1: Can't query large data
        codebase = open("huge_codebase.txt").read()  # 500K tokens
        # ❌ Context overflow - can't fit in LLM window

        # Problem 2: No memory across sessions
        # ❌ Each session starts from scratch
        # ❌ Same questions = same work redone

        # Problem 3: No learning
        # ❌ Mistakes repeated
        # ❌ Patterns not recognized
        # ❌ No improvement over time

        # Problem 4: Manual context management
        # ❌ Developer must decide what to include
        # ❌ Token budget exceeded or wasted
        # ❌ Relevant info often missed
```

### With Cognition Architecture (The Solution)

```python
# WITH COGNITION: Agent has memory, reflection, smart context

from dana.core.agent import STARAgent
from dana.core.memory import LTMemory
from dana.common.resource import RLMResource
from dana.core.knowledge.prompts.codecs import CSXMLCodec

# Create agent with cognition and codec system
agent = STARAgent(
    name="cognitive_agent",
    codec=CSXMLCodec,  # Enable structured LLM communication
    ltmemory_path="./agent_memories/"  # Persistent memory!
)

# Attach large data sources (queried via RLM, not stuffed in context)
agent.with_resources(RLMResource(file="huge_codebase.md"))

# === Week 1: First auth bug ===
agent.run("Find the auth bug")
# ✅ RLM queries 500K codebase: "What handles auth?"
# ✅ Agent finds: "Token expiry not checked"
# ✅ Session ends → Reflection stores lesson to LTMemory

# === Week 2: Similar bug ===
agent.run("Users getting logged out unexpectedly")
# ✅ ContextBuilder queries LTMemory: "What do I know about auth?"
# ✅ Returns: "Auth bugs often relate to token expiry"
# ✅ Agent checks expiry FIRST (learned from Week 1!)
# ✅ Finds bug faster, stores new pattern

# === Week 3: Pattern recognized ===
agent.run("Another auth issue")
# ✅ LTMemory: "3 token expiry issues → suggest systematic fix"
# ✅ Agent proactively: "Should we add token validation middleware?"
# ✅ Agent has EVOLVED from bug-fixer to problem-preventer
```

### Full Demo Code

```python
from dana.core.memory import STMemory, LTMemory
from dana.core.context import ContextBuilder
from dana.core.reflection import Reflection
from dana.common.resource import RLMResource

# === Session 1 ===
stmem = STMemory(max_entries=100)
ltmem = LTMemory(path="./memories/")
codebase = RLMResource(file="codebase.md")

# During session...
stmem.append("user", "Find auth bugs")
stmem.append("agent", "Searching codebase...")
stmem.append("observation", "Token expiry not validated in refresh flow")
stmem.append("agent", "Fixed by adding expiry check")

# Build context for LLM (smart assembly)
ctx = ContextBuilder(token_budget=50000)
ctx.add_source("stmemory", stmem)         # Direct inclusion
ctx.add_source("ltmemory", ltmem)         # RLM query
ctx.add_source("codebase", codebase)      # RLM query
context = ctx.build(task="Verify the fix is complete")

# End session → Reflect
reflection = Reflection()
result = reflection.run(stmemory=stmem, ltmemory=ltmem)
# → Stores: "lesson: token expiry bugs in auth module"

# === Session 2 (next week) ===
ltmem = LTMemory(path="./memories/")  # Same path = remembers!
past_knowledge = ltmem.query("auth issues")
# → Returns: "Token expiry bugs are common in auth module"
# Agent now starts with this context!
```

### Examples Directory Structure

```
examples/cognition/
├── data_rlm/
│   ├── query_large_codebase.py      # RLM basics
│   └── sample_codebase.md
├── memory/
│   ├── agent_with_memory.py         # STMemory + LTMemory
│   ├── stmemory_basics.py
│   └── ltmemory_persistence.py
├── context/
│   ├── smart_context_assembly.py    # ContextBuilder demo
│   └── token_budget_demo.py
├── reflection/
│   ├── session_learning.py          # 4-phase reflection
│   └── learner_integration.py
└── full_system/
    └── cognitive_agent.py           # Everything together
```

**Demo narrative**: "Watch an agent evolve from stateless tool to learning system that remembers, reflects, and improves."
