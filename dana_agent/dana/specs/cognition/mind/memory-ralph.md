# Memory - Implementation Spec

**Status: ✅ COMPLETE** (Core implementation and STARAgent integration done)

## Goal

Implement a two-tier memory system for Dana agents: stmemory (session timeline) and ltmemory (persistent knowledge store).

## Demo

Run: `examples/cognition/memory/agent_with_memory.py`

### Without Memory (The Problem)

```python
# WITHOUT MEMORY: Agent forgets everything between sessions

# Session 1: Debug auth issue
agent.run("Find the auth bug")
# Agent discovers: "Token expiry not checked in refresh flow"
# Agent fixes it successfully
# Session ends... knowledge is LOST

# Session 2: Same type of bug appears
agent.run("Users are getting logged out unexpectedly")
# ❌ Agent starts from scratch - doesn't remember the pattern
# ❌ Wastes time rediscovering: "Oh, it's token expiry again"
# ❌ No learning across sessions
```

### With Memory (The Solution)

```python
# WITH MEMORY: Agent remembers and learns

from dana.core.memory import STMemory, LTMemory

# === Session 1 ===
stmem = STMemory(max_entries=100)   # Track this session
ltmem = LTMemory(path="./memories/") # Persist across sessions

stmem.append("user", "Find the auth bug")
stmem.append("agent", "Searching codebase...")
stmem.append("observation", "Token expiry not checked in refresh flow")
stmem.append("agent", "Fixed by adding expiry validation")

# End of session: Reflection stores lesson to ltmemory
ltmem.store({
    "type": "lesson",
    "content": "Auth bugs often relate to token expiry edge cases",
    "context": "debugging session"
})

# === Session 2 (days later) ===
ltmem = LTMemory(path="./memories/")  # Same path = same memories

# Agent queries past knowledge
past = ltmem.query("What do I know about auth issues?")
# ✅ Returns: "Auth bugs often relate to token expiry edge cases"
# ✅ Agent immediately checks token expiry
# ✅ Finds issue faster because it LEARNED from Session 1
```

### What You'll See

```
Session Timeline (STMemory):
  [user] Find the auth bug
  [agent] Searching codebase...
  [observation] Token expiry not checked
  [agent] Fixed by adding validation

Stored Memories (LTMemory): 3 total
  [lesson] Auth bugs often relate to token expiry...
  [episode] Helped user debug logout issue...
  [fact] Auth module uses JWT with 1hr expiry...
```

## MVP Requirements

### 1. STMemory (`dana_agent/dana/core/memory/stmemory.py`)

```python
@dataclass
class MemoryEntry:
    """Single memory entry."""
    role: str        # user, agent, observation, system
    content: str
    timestamp: datetime

class STMemory:
    """Short-term session memory."""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.entries: list[MemoryEntry] = []

    def append(self, role: str, content: str) -> None:
        """Add entry to timeline. Drops oldest if over limit."""

    def recent(self, n: int = 10) -> list[MemoryEntry]:
        """Get n most recent entries."""

    @property
    def timeline(self) -> list[MemoryEntry]:
        """Full timeline."""

    def estimate_tokens(self) -> int:
        """Estimate token count for context building."""

    def clear(self) -> None:
        """Clear all entries."""

    def to_text(self) -> str:
        """Format timeline as text for context inclusion."""

    def __len__(self) -> int:
        return len(self.entries)
```

Requirements:
- [x] Append entries with auto-timestamp
- [x] Enforce max_entries limit (drop oldest)
- [x] Query recent N entries
- [x] Estimate token count
- [x] Format as text for context inclusion
- [x] Clear all entries

### 2. LTMemory (`dana_agent/dana/core/memory/ltmemory.py`)

```python
class LTMemory:
    """Long-term persistent memory."""

    def __init__(self, path: str = "./memories/"):
        self.path = Path(path)
        self.memories_file = self.path / "memories.md"

    def store(self, memory: dict) -> None:
        """
        Persist a memory. Expected fields:
        - type: str (lesson, episode, fact, pattern)
        - content: str
        - context: str (optional)
        - timestamp: str (optional, auto-generated)
        """

    def query(self, question: str) -> str:
        """
        Query memories using RLM pattern.
        Returns relevant memories as text.
        """

    def count(self) -> int:
        """Number of stored memories."""
```

Requirements:
- [x] Store memories to markdown file (append)
- [x] Auto-generate timestamp if not provided
- [x] Query via RLM (reuse RLMResource internally)
- [x] Create storage directory if missing
- [x] Count stored memories

### 3. Memory Entry Format (in memories.md)

```markdown
## Memory [2024-01-15T10:30:00Z]
- **Type**: lesson
- **Context**: debugging session
- **Content**: Auth bugs often relate to token expiry edge cases

---

## Memory [2024-01-15T11:00:00Z]
- **Type**: episode
- **Context**: user request
- **Content**: User asked about performance. Found N+1 query issue.

---
```

Requirements:
- [x] Human-readable format
- [x] Parseable by RLM queries
- [x] Timestamped entries
- [x] Separator between entries

## Example Files (`examples/cognition/memory/`)

- `agent_with_memory.py` - Full demo with STMemory + LTMemory
- `stmemory_basics.py` - Session timeline tracking
- `ltmemory_persistence.py` - Cross-session memory recall
- `staragent_with_ltmemory.py` - STARAgent with LTMemory integration demo

## Files Implemented

- `dana_agent/dana/core/memory/stmemory.py` ✅
- `dana_agent/dana/core/memory/ltmemory.py` ✅
- `dana_agent/dana/core/memory/__init__.py` ✅
- `examples/cognition/memory/` ✅

## Tests Required

Create `dana_agent/tests/unit/test_stmemory.py`:
- [x] test_append - adds entry with timestamp
- [x] test_max_entries - drops oldest when limit exceeded
- [x] test_recent - returns N most recent
- [x] test_timeline - returns all entries
- [x] test_estimate_tokens - returns reasonable estimate
- [x] test_to_text - formats as readable text
- [x] test_clear - removes all entries
- [x] test_len - returns entry count

Create `dana_agent/tests/unit/test_ltmemory.py`:
- [x] test_store - persists memory to file
- [x] test_store_auto_timestamp - generates timestamp if missing
- [x] test_query - retrieves relevant memories
- [x] test_creates_directory - creates path if missing
- [x] test_count - returns memory count

Create `dana_agent/tests/unit/test_staragent_ltmemory.py`:
- [x] test_staragent_with_ltmemory_path - STARAgent creates LTMemory
- [x] test_staragent_without_ltmemory_path - STARAgent works without LTMemory
- [x] test_reflect_retentive_stores_memories - Learner stores to LTMemory
- [x] test_query_learnings_retentive_phase - Learner queries LTMemory
- [x] test_default_learner_query_learnings - DefaultLearner queries LTMemory

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_stmemory.py tests/unit/test_ltmemory.py tests/unit/test_staragent_ltmemory.py -v`

## Success Criteria

1. All tests pass
2. stmemory tracks session timeline with size limit
3. ltmemory persists memories to file
4. ltmemory queries via RLM
5. Example runs and demonstrates both memory types

## Before Marking Complete

- [x] Review code for KISS/YAGNI compliance
- [x] Simplify any overly complex implementations
- [x] Remove unnecessary abstractions
- [x] Ensure code is readable and maintainable

## When Complete

**You MUST run tests before marking complete:**
```bash
cd dana_agent && uv run pytest tests/unit/test_stmemory.py tests/unit/test_ltmemory.py tests/unit/test_staragent_ltmemory.py -v
```

Only if ALL tests pass, output exactly:
<promise>MEMORY COMPLETE</promise>

## STARAgent Integration

### Current State
- ✅ STMemory implemented at `dana.core.memory.stmemory`
- ✅ LTMemory implemented at `dana.core.memory.ltmemory`
- ✅ STARAgent accepts `ltmemory_path` parameter
- ✅ Learner stores memories to LTMemory in RETENTIVE phase
- ✅ PromptEngineer queries LTMemory for past knowledge
- ⏸️ Timeline/STMemory unification deferred (both serve different purposes)

### Integration Tasks

| Task | Status | Description |
|------|--------|-------------|
| Add LTMemory to STARAgent | ✅ Done | Accept `ltmemory_path` in constructor |
| Wire Learner to LTMemory | ✅ Done | Retentive phase persists to LTMemory |
| Query LTMemory in context | ✅ Done | PromptEngineer includes past knowledge |
| Timeline/STMemory unification | ⏸️ Deferred | Timeline for agent internals, STMemory for simple use cases |

### Integration Code

```python
# In star_agent.py __init__
from dana.core.memory import LTMemory

class STARAgent:
    def __init__(
        self,
        ...,
        ltmemory_path: str | None = None,  # NEW
    ):
        # Existing timeline
        self._timeline = Timeline(...)

        # NEW: Long-term memory
        if ltmemory_path:
            self._ltmemory = LTMemory(path=ltmemory_path)
        else:
            self._ltmemory = None
```

```python
# In learner.py _reflect_retentive
def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
    # ... existing logic ...

    # NEW: Persist to LTMemory if available
    if hasattr(self._agent, '_ltmemory') and self._agent._ltmemory:
        for memory in memories_to_store:
            self._agent._ltmemory.store(memory)
```

### Files Implemented
- `dana_agent/dana/core/memory/stmemory.py` ✅
- `dana_agent/dana/core/memory/ltmemory.py` ✅
- `dana_agent/dana/core/memory/__init__.py` ✅

## References

- PRD: [memory-prd.md](./memory-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [data-ralph.md](../data/data-ralph.md) (RLM for ltmemory queries)
