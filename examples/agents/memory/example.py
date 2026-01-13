"""
Example demonstrating Dana's two-tier memory system.

This example shows:
- STMemory: Session timeline tracking with size limits
- LTMemory: Persistent knowledge store with RLM-based querying
"""

import tempfile
from pathlib import Path

from dana.core.memory import LTMemory, STMemory


def demo_stmemory():
    """Demonstrate short-term memory (session timeline)."""
    print("=" * 60)
    print("=== Short-term memory (session) ===")
    print("=" * 60)

    stmem = STMemory(max_entries=100)

    # Record session timeline
    stmem.append("user", "Find bugs in auth module")
    stmem.append("agent", "Searching codebase...")
    stmem.append("observation", "Found 3 potential issues")
    stmem.append("agent", "Issue 1: Token expiry not checked")

    # Query recent history
    print("\nRecent 3 entries:")
    for entry in stmem.recent(3):
        print(f"  [{entry.role}] {entry.content}")

    print(f"\nTimeline entries: {len(stmem)}")
    print(f"Tokens estimate: {stmem.estimate_tokens()}")

    # Show formatted timeline
    print("\nFormatted timeline:")
    print(stmem.to_text())


def demo_ltmemory():
    """Demonstrate long-term memory (persistent knowledge)."""
    print("\n" + "=" * 60)
    print("=== Long-term memory (persistent) ===")
    print("=" * 60)

    # Use temp directory for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        ltmem = LTMemory(path=tmpdir)

        # Store memories
        ltmem.store({
            "type": "lesson",
            "content": "Auth bugs often relate to token expiry edge cases",
            "context": "debugging session",
            "timestamp": "2024-01-15T10:30:00Z",
        })

        ltmem.store({
            "type": "episode",
            "content": "User asked about performance. Found N+1 query issue in user list endpoint.",
            "context": "performance review",
            "timestamp": "2024-01-15T14:00:00Z",
        })

        ltmem.store({
            "type": "fact",
            "content": "The auth module uses JWT tokens with 1-hour expiry",
            "context": "code exploration",
            "timestamp": "2024-01-16T09:00:00Z",
        })

        print(f"\nStored memories: {ltmem.count()}")

        # Show what's stored
        print("\nMemories file content:")
        print("-" * 40)
        print(ltmem.memories_file.read_text())

        # Note: Query requires API key and makes actual LLM calls
        print("\nTo query memories (requires API key):")
        print('  result = ltmem.query("What do I know about auth bugs?")')
        print('  # Returns: "Based on past experience: Auth bugs often relate to..."')


def main():
    """Run memory demonstrations."""
    print("\nDana Memory System Demo")
    print("=" * 60)

    demo_stmemory()
    demo_ltmemory()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
