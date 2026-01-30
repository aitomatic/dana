"""Semantic memory store for Dana agents.

A persistent, queryable memory store that any agent can use.
Supports semantic search using vector embeddings (OpenAI or local).

Requires: pip install dana[memory]

Usage:
    from dana.lib.memory import MemoryStore, Memory

    # Create store (uses ~/.dana/memory by default)
    store = MemoryStore()

    # Store a memory
    memory = store.store(
        "When VAV damper is at 100% but zone is warm, check AHU first",
        identity="hvac",
        source="session",
    )

    # Query for relevant memories
    results = store.query("debugging VAV temperature issues", limit=3)
    for memory in results:
        print(f"[{memory.score:.2f}] {memory.text}")

    # Index a directory of markdown files
    store.index_directory("./learnings/", identity="ontologist")

CLI:
    dana-memory store "memory text" --identity hvac
    dana-memory query "query text" --limit 3 --json
    dana-memory index ./docs/ --identity docs
    dana-memory status
"""

# Memory module requires optional dependencies (lancedb, sentence-transformers)
# Import lazily to avoid errors when dependencies aren't installed
try:
    from .store import Memory, MemoryStore

    _AVAILABLE = True
except ImportError:
    Memory = None  # type: ignore
    MemoryStore = None  # type: ignore
    _AVAILABLE = False

__all__ = ["MemoryStore", "Memory", "available"]


def available() -> bool:
    """Check if memory module dependencies are installed."""
    return _AVAILABLE
