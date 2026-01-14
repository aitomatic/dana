#!/usr/bin/env python3
"""
STARAgent with LTMemory - Integration Demo

Demonstrates how to create a STARAgent with long-term memory enabled,
allowing the agent to learn and remember across sessions.

This example shows the integration between STARAgent and LTMemory:
- ltmemory_path enables persistent cross-session learning
- The Learner's RETENTIVE phase automatically stores memories
- PromptEngineer queries LTMemory for relevant past knowledge
"""

import tempfile
from pathlib import Path

# Note: This is a demonstration of the STARAgent configuration.
# Running it requires API keys and would make actual LLM calls.


def show_staragent_configuration():
    """Show how to configure STARAgent with LTMemory."""
    print("=" * 60)
    print("STARAgent with LTMemory - Configuration Demo")
    print("=" * 60)

    print("""
## Creating a STARAgent with Long-Term Memory

```python
from dana.core.agent import STARAgent
from dana.core.agent.components.learner import DefaultLearner

# Create agent with LTMemory enabled
agent = STARAgent(
    agent_type="my_agent",
    llm_provider="anthropic",
    model="claude-sonnet-4-20250514",
    ltmemory_path="./memories/",  # <-- Enable LTMemory
    learner=DefaultLearner(agent=None),  # <-- Learner handles memory storage
)
```

## What Happens Behind the Scenes

1. **On Creation**:
   - STARAgent creates an LTMemory instance at the specified path
   - LTMemory uses RLM (Recursive Language Model) for semantic queries

2. **During REFLECT Phase (RETENTIVE)**:
   - The Learner extracts key learnings from the interaction
   - Episodes and patterns are automatically stored to LTMemory

3. **On Next Query**:
   - PromptEngineer queries LTMemory for relevant past knowledge
   - Past learnings are included in the context for the LLM

## Memory Storage Format

Memories are stored in human-readable markdown at `{ltmemory_path}/memories.md`:

```markdown
## Memory [2024-01-15T10:30:00Z]
- **Type**: episode
- **Context**: session interaction
- **Content**: User asked: Find the auth bug Used tools: file_search Response: Found issue in token.py

---

## Memory [2024-01-15T10:30:01Z]
- **Type**: pattern
- **Context**: tool usage pattern
- **Content**: Successfully used tools: resource

---
```

## Key Benefits

1. **Cross-Session Learning**: Agent remembers lessons from past sessions
2. **Automatic Memory Storage**: No manual intervention needed
3. **Semantic Retrieval**: RLM enables intelligent memory queries
4. **Persistent Knowledge**: Survives across restarts and sessions
""")


def show_memory_flow():
    """Show the memory flow in STARAgent."""
    print("\n" + "=" * 60)
    print("Memory Flow in STARAgent")
    print("=" * 60)

    print("""
Session 1: User asks "Find the auth bug"
┌─────────────────────────────────────────────────────────┐
│  STARAgent with ltmemory_path="./memories/"             │
├─────────────────────────────────────────────────────────┤
│  SEE: Perceive user input                               │
│    └─> Timeline: [user: "Find the auth bug"]            │
│                                                         │
│  THINK: Query LLM                                       │
│    └─> PromptEngineer queries LTMemory                  │
│        (No memories yet - first session)                │
│                                                         │
│  ACT: Execute tools                                     │
│    └─> file_search, read_file, etc.                     │
│                                                         │
│  REFLECT (RETENTIVE):                                   │
│    └─> DefaultLearner stores to LTMemory:               │
│        - Episode: "User asked about auth bug..."        │
│        - Pattern: "Successfully used file_search"       │
└─────────────────────────────────────────────────────────┘
         │
         ▼ memories.md updated

Session 2: User asks "Users getting logged out"
┌─────────────────────────────────────────────────────────┐
│  STARAgent with ltmemory_path="./memories/"             │
├─────────────────────────────────────────────────────────┤
│  SEE: Perceive user input                               │
│                                                         │
│  THINK: Query LLM                                       │
│    └─> PromptEngineer queries LTMemory                  │
│        ✓ Returns: "User asked about auth bug..."        │
│        ✓ Agent has context from Session 1!             │
│                                                         │
│  ACT: Execute tools (faster - has prior knowledge)      │
│                                                         │
│  REFLECT (RETENTIVE): Stores new learnings              │
└─────────────────────────────────────────────────────────┘
""")


def show_direct_ltmemory_usage():
    """Show how to directly use LTMemory with STARAgent."""
    print("\n" + "=" * 60)
    print("Direct LTMemory Access")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nUsing temp directory: {tmpdir}")

        # Import with mocked RLM to avoid API calls
        from unittest.mock import MagicMock, patch

        with patch("dana.core.memory.ltmemory.RLMResource"):
            from dana.core.memory import LTMemory

            ltmem = LTMemory(path=tmpdir)

            # Store some memories
            ltmem.store({
                "type": "lesson",
                "content": "Auth bugs often relate to token expiry",
                "context": "debugging session",
            })
            ltmem.store({
                "type": "episode",
                "content": "Fixed N+1 query in user dashboard",
                "context": "performance optimization",
            })

            print(f"\nStored {ltmem.count()} memories")
            print(f"\nMemory file contents:")
            print("-" * 40)
            print(ltmem.memories_file.read_text())
            print("-" * 40)


def main():
    show_staragent_configuration()
    show_memory_flow()
    show_direct_ltmemory_usage()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo use STARAgent with LTMemory in your code:")
    print("  agent = STARAgent(ltmemory_path='./memories/', ...)")
    print("\nThe agent will automatically learn and remember across sessions!")


if __name__ == "__main__":
    main()
