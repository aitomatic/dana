# Memory - Product Requirements Document

## Overview

Memory is the agent's internal storage for experiences and knowledge. Unlike Data (external), Memory is owned by the agent and evolves over time through Reflection.

```
                    ┌────────────┐
                    │ Reflection │
                    └─────┬──────┘
                          ▼ (distillation)
┌─────────────────────────────────────────┐
│                 MEMORY                  │
├───────────────────┬─────────────────────┤
│     stmemory      │      ltmemory       │
│   (short-term)    │    (long-term)      │
├───────────────────┼─────────────────────┤
│ Live session      │ Distilled episodes  │
│ Timeline          │ Integrated patterns │
│ Working state     │ Retained knowledge  │
├───────────────────┼─────────────────────┤
│ Session-scoped    │ Persistent          │
│ Configurable size │ Large               │
└───────────────────┴─────────────────────┘
```

## Problem Statement

Dana agents currently have no memory across interactions:
- Session state is lost when conversation ends
- Agents can't learn from past experiences
- No way to accumulate knowledge over time
- Each session starts from scratch

## Solution

Implement a two-tier memory system:
1. **stmemory**: Session timeline and working state (configurable size)
2. **ltmemory**: Persistent storage for distilled knowledge

Reflection (separate component) processes stmemory into ltmemory.

## User Stories

1. **As an agent**, I want to remember what happened earlier in this session so I can maintain continuity.

2. **As an agent**, I want to recall relevant past experiences so I can apply learned patterns.

3. **As a user**, I want the agent to remember our past interactions so I don't repeat myself.

4. **As a developer**, I want to configure how much session history to retain in stmemory.

## Use Cases

| Scenario | Memory Use |
|----------|------------|
| Multi-turn conversation | stmemory tracks dialogue history |
| Recurring task | ltmemory recalls past approaches |
| Learning from mistakes | ltmemory stores lessons learned |
| User preferences | ltmemory retains user-specific knowledge |

## Requirements

### Functional

**stmemory:**
- Store session timeline (events, actions, observations)
- Configurable size limit
- Append new entries
- Query recent history
- Clear on session end (or persist if configured)

**ltmemory:**
- Persistent storage (survives sessions)
- Store structured memories (episodes, patterns, facts)
- Query by similarity or RLM (size-dependent)
- Accept new memories from Reflection

### Non-Functional
- stmemory access < 10ms (in-memory)
- ltmemory query < 500ms (vector) or < 10s (RLM)
- Storage format: JSON or markdown files (MVP)

## Success Metrics

1. **Continuity**: Agent maintains context within session
2. **Recall**: Agent retrieves relevant past experiences
3. **Growth**: ltmemory accumulates useful knowledge over time

## Scope

### In MVP
- stmemory: in-memory timeline with append/query
- stmemory: configurable size limit
- ltmemory: file-based storage (markdown/JSON)
- ltmemory: simple append (Reflection writes to it)
- ltmemory: RLM-based query (reuse Data access pattern)

### Out of MVP (Future)
- Vector-based ltmemory retrieval
- Memory importance scoring
- Automatic forgetting / garbage collection
- Memory compression
- Cross-session stmemory persistence

## STARAgent Integration

### Current State

STARAgent has a `Timeline` component that serves a similar purpose to STMemory:

| Aspect | Timeline | STMemory |
|--------|----------|----------|
| Purpose | Track conversation history | Track session events |
| Storage | `TimelineEntry` objects | `MemoryEntry` objects |
| Entry types | Rich types (USER_MESSAGE, AGENT_RESPONSE, TOOL_CALL, etc.) | Simple roles (user, agent, observation, system) |
| Persistence | Saves to repository | In-memory only |
| Token tracking | Yes | Yes (estimate) |

### Integration Approach

**Option A: Timeline wraps STMemory** (Recommended)
- Timeline becomes a richer interface over STMemory
- STMemory handles core storage, Timeline adds entry types and persistence
- Minimal changes to STARAgent

**Option B: Replace Timeline with STMemory**
- Simpler architecture but loses Timeline's rich entry types
- Would require adapting all Timeline usage in STARAgent

**Option C: Parallel systems**
- Keep both, sync between them
- Most complex, not recommended

### Integration Requirements

1. **LTMemory in STARAgent**
   ```python
   class STARAgent:
       def __init__(self, ..., ltmemory_path: str | None = None):
           self._ltmemory = LTMemory(path=ltmemory_path) if ltmemory_path else None
   ```

2. **LTMemory for Context Building**
   - ContextBuilder should query LTMemory for relevant past knowledge
   - Include in system prompt or as separate context section

3. **LTMemory for Reflection**
   - Learner's retentive phase should persist insights to LTMemory
   - Integrative phase should query LTMemory for connections

## Demo

When Memory MVP is complete, we can demonstrate:

```python
from dana.core.memory import STMemory, LTMemory

# Session memory
stmem = STMemory(max_entries=100)
stmem.append("user", "How do I fix the auth bug?")
stmem.append("agent", "Let me check the codebase...")
stmem.append("observation", "Found issue in token validation")

print(stmem.recent(5))  # Last 5 entries
print(stmem.timeline)   # Full session timeline

# Long-term memory
ltmem = LTMemory(path="memories/")
ltmem.store({
    "type": "lesson",
    "content": "Token validation bugs often stem from timezone issues",
    "source": "session_123"
})

# Query (uses RLM for large memory stores)
result = ltmem.query("What do I know about authentication bugs?")
print(result)
# → "From past sessions: token validation bugs often stem from..."
```

**Demo narrative**: "Agent remembers this session's context (stmemory) and recalls lessons from past sessions (ltmemory)."

## References

- Implementation spec: [memory-ralph.md](./memory-ralph.md)
- Parent: [mind overview](./overview.md)
- Fed by: [reflection](./reflection-prd.md)
- Used by: [context](./context-prd.md)
