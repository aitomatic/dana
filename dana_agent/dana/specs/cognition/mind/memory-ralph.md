# Memory - Implementation Spec

## Goal

Implement a two-tier memory system for Dana agents: stmemory (session timeline) and ltmemory (persistent knowledge store).

## Demo

When complete, run `examples/agents/memory/example.py`:

```python
from dana.core.memory import STMemory, LTMemory

# === Short-term memory (session) ===
stmem = STMemory(max_entries=100)

# Record session timeline
stmem.append("user", "Find bugs in auth module")
stmem.append("agent", "Searching codebase...")
stmem.append("observation", "Found 3 potential issues")
stmem.append("agent", "Issue 1: Token expiry not checked")

# Query recent history
print(stmem.recent(3))
# → [observation: Found 3..., agent: Issue 1...]

print(f"Timeline entries: {len(stmem)}")
print(f"Tokens estimate: {stmem.estimate_tokens()}")

# === Long-term memory (persistent) ===
ltmem = LTMemory(path="./agent_memory/")

# Store a memory (typically done by Reflection)
ltmem.store({
    "type": "lesson",
    "content": "Auth bugs often relate to token expiry edge cases",
    "context": "debugging session",
    "timestamp": "2024-01-15T10:30:00Z"
})

# Query memories (RLM for large stores)
result = ltmem.query("What do I know about auth bugs?")
print(result)
# → "Based on past experience: Auth bugs often relate to..."
```

**What you'll see**: stmemory tracking session events, ltmemory persisting and recalling past lessons.

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

## Current Progress

Check these files to see what exists:
- `dana_agent/dana/core/memory/stmemory.py`
- `dana_agent/dana/core/memory/ltmemory.py`
- `dana_agent/dana/core/memory/__init__.py`
- `examples/agents/memory/`

Update checkboxes above as you complete each requirement.

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

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_stmemory.py tests/unit/test_ltmemory.py -v`

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

<promise>MEMORY COMPLETE</promise>

## References

- PRD: [memory-prd.md](./memory-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [data-ralph.md](../data/data-ralph.md) (RLM for ltmemory queries)
