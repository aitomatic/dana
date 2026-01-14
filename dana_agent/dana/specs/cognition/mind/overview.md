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

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Memory | ✅ Complete | STMemory + LTMemory implemented |
| Context | ✅ Complete | ContextBuilder implemented and integrated in LocalPromptAPI (with codec) |
| Reflection | ✅ Complete | Integrated via Learner (persists to LTMemory), standalone Reflection class also available |

## STARAgent Integration Status

STARAgent supports two modes based on whether a codec is provided:

| Mode | Prompt System | Tool Caller | Status |
|------|---------------|-------------|--------|
| **With codec** | `LocalPromptAPI` | `CodecToolCaller` | ✅ Primary (recommended) |
| **Without codec** | `PromptEngineer` | `ToolCaller` | ⚠️ Legacy only |

| Mind Component | STARAgent Equivalent | Integration |
|----------------|---------------------|-------------|
| STMemory | `Timeline` | ⚠️ Parallel implementations (both serve different purposes) |
| LTMemory | `_ltmemory` | ✅ Integrated via `ltmemory_path` parameter |
| ContextBuilder | `LocalPromptAPI` | ✅ Integrated - used in `build_llm_request()` (with codec) |
| Reflection | `Learner` | ✅ Integrated - persists to LTMemory in RETENTIVE phase |

### Integration Details

1. **LTMemory → STARAgent**: ✅ Complete - `ltmemory_path` parameter in constructor
2. **Learner → LTMemory**: ✅ Complete - RETENTIVE phase persists memories
3. **ContextBuilder**: ✅ Complete - Integrated in LocalPromptAPI (when using codec)
4. **Timeline/STMemory**: ⚠️ Both exist - Timeline for agent internals, STMemory for simple use cases
5. **Codec System**: ✅ CSXMLCodec provides structured LLM communication format

## Specs

| Component | PRD | Implementation | Status |
|-----------|-----|----------------|--------|
| Memory | [memory-prd.md](./memory-prd.md) | [memory-ralph.md](./memory-ralph.md) | ✅ |
| Context | [context-prd.md](./context-prd.md) | [context-ralph.md](./context-ralph.md) | ✅ |
| Reflection | [reflection-prd.md](./reflection-prd.md) | [reflection-ralph.md](./reflection-ralph.md) | ✅ |
