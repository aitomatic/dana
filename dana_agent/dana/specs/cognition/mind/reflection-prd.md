# Reflection - Product Requirements Document

## Overview

Reflection is the **process** that transforms experiences into memory. It's not storage - it's the distillation pipeline that runs at strategic moments to extract insights from stmemory into ltmemory.

```
Experience → stmemory
                │
                ▼ (reflection invoked)
         ┌──────────────┐
         │ Acquisitive  │ → what's new/worth capturing?
         │ Episodic     │ → what happened?
         │ Integrative  │ → how does it connect?
         │ Retentive    │ → what to keep?
         └──────────────┘
                │
                ▼ (distillation)
            ltmemory
```

## Problem Statement

Without reflection, agents either:
- Store everything (bloated, noisy ltmemory)
- Store nothing (no learning)
- Require manual curation of what to remember

Reflection automates the "thinking about what happened" process that humans do naturally.

## Solution

Implement a Reflection process with four phases:

| Phase | Question | Output |
|-------|----------|--------|
| Acquisitive | What's new or worth capturing? | Candidate memories |
| Episodic | What happened? (narrative) | Episode summaries |
| Integrative | How does this connect to existing knowledge? | Patterns, links |
| Retentive | What should be kept long-term? | Filtered memories → ltmemory |

## When Reflection Runs

Reflection is invoked at **strategic moments**, not continuously:

| Trigger | Rationale |
|---------|-----------|
| Session end | Natural boundary, time to consolidate |
| Task completion | Milestone achieved, lessons to capture |
| Explicit request | User/agent says "reflect on this" |
| Threshold reached | stmemory size exceeds limit |
| Scheduled | Periodic (e.g., daily) consolidation |

## User Stories

1. **As an agent**, I want to automatically extract lessons from completed tasks so I improve over time.

2. **As an agent**, I want to consolidate session history into durable memories so I don't lose insights.

3. **As a developer**, I want to trigger reflection at appropriate moments so the agent learns efficiently.

4. **As a user**, I want the agent to remember important things without remembering everything.

## Phases Explained

### Acquisitive
Scans stmemory for noteworthy content:
- New information learned
- Corrections received
- User preferences expressed
- Unexpected outcomes

### Episodic
Captures what happened as narrative:
- Task attempted and outcome
- Key steps taken
- Obstacles encountered
- Decisions made

### Integrative
Connects new experience to existing knowledge:
- Similar past experiences
- Patterns emerging
- Contradictions to resolve
- Knowledge to update

### Retentive
Filters what actually gets stored:
- Is this worth remembering?
- Is it already known?
- How important is it?
- What's the minimal form?

## Requirements

### Functional
- Accept stmemory as input
- Accept ltmemory for integration queries
- Run four phases in sequence
- Output structured memories for ltmemory storage
- Return reflection summary

### Non-Functional
- Use LLM for each phase (semantic understanding required)
- Configurable phase prompts
- Total reflection time < 30s for typical session
- Idempotent (re-running doesn't duplicate memories)

## Success Metrics

1. **Signal-to-noise**: ltmemory contains useful, not redundant memories
2. **Coverage**: Important lessons captured, not missed
3. **Integration**: New memories connect to existing knowledge

## Scope

### In MVP
- All four phases implemented
- LLM-based phase execution
- stmemory → ltmemory pipeline
- Manual trigger (explicit call)
- Basic prompts for each phase

### Out of MVP (Future)
- Automatic triggers (session end, threshold)
- Importance scoring
- Duplicate detection
- Memory consolidation (merging related memories)
- Phase customization per agent type

## Demo

When Reflection MVP is complete, we can demonstrate:

```python
from dana.core.memory import STMemory, LTMemory
from dana.core.reflection import Reflection

# Session with some experiences
stmem = STMemory()
stmem.append("user", "How do I fix the N+1 query?")
stmem.append("agent", "Found the issue in user_loader.py")
stmem.append("observation", "Added .prefetch_related(), 10x speedup")
stmem.append("user", "That worked, thanks!")

# Long-term memory (may have existing knowledge)
ltmem = LTMemory(path="./memories/")

# Run reflection
reflection = Reflection(llm_model="claude-sonnet-4-20250514")
result = reflection.run(stmemory=stmem, ltmemory=ltmem)

print(result.summary)
# → "Session involved fixing N+1 query. Key lesson captured."

print(result.memories_created)
# → [
#     {type: "lesson", content: "N+1 queries fixed with prefetch_related()"},
#     {type: "episode", content: "Helped user optimize database query..."}
#   ]

# Memories automatically stored in ltmemory
print(ltmem.count())  # Now has new memories
```

**Demo narrative**: "Agent reflects on session, extracts lessons and episodes, stores to long-term memory. Next session, it can recall these."

## References

- Implementation spec: [reflection-ralph.md](./reflection-ralph.md)
- Parent: [mind overview](./overview.md)
- Reads from: [stmemory](./memory-prd.md)
- Writes to: [ltmemory](./memory-prd.md)
