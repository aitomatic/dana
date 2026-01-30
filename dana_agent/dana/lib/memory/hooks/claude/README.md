# Dana Memory Hooks for Claude Code

Two hooks that enable persistent memory across Claude Code sessions:

| Hook | File | Purpose |
|------|------|---------|
| PreToolUse | `PreToolUseHook-Memory.py` | **RECALL** - retrieves relevant memories before tool use |
| Stop | `StopHook-Memory.py` | **STORE** - saves `[REMEMBER: ...]` patterns after Claude's turn |

## Installation

```bash
# Copy hooks to Claude Code hooks directory
cp PreToolUseHook-Memory.py ~/.claude/hooks/
cp StopHook-Memory.py ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/PreToolUseHook-Memory.py
chmod +x ~/.claude/hooks/StopHook-Memory.py
```

## Configuration

Add to your shell profile or `.env`:

```bash
# Enable memory system
DANA_MEMORY_ENABLED=1

# Path to dana project (required if dana-memory not in PATH)
DANA_PROJECT_PATH=~/src/aitomatic/dana-internal

# Recall settings
DANA_MEMORY_LIMIT=3           # Max memories per tool call
DANA_MEMORY_MAX_WORDS=1500    # Max total words in payload
DANA_MEMORY_MIN_SCORE=0.3     # Similarity threshold

# Store settings
DANA_MEMORY_IDENTITY=agent    # Default identity for stored memories
```

## CLAUDE.md Instructions

Add this to your project's `CLAUDE.md` to teach Claude how to use the memory system:

```markdown
## Memory System

This project uses dana-memory for persistent knowledge across sessions.

**Memories are automatically retrieved** when relevant to your current task.

**To save something important**, include this pattern in your response:

    [REMEMBER: description of what to remember]

Or with a specific identity:

    [REMEMBER identity=coding: Always run tests before committing]

Use this when you discover:
- Project conventions or patterns
- User preferences
- Solutions to tricky bugs
- Important architectural decisions
- Recurring issues and their fixes

Keep memories concise and actionable. Bad: "The user mentioned something about tests."
Good: "Run pytest with --tb=short flag in this project."
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code Session                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User prompt ──► Claude thinks ──► Tool use ──► Response        │
│                        │              │              │          │
│                        │              │              │          │
│                        ▼              │              ▼          │
│               ┌────────────────┐      │      ┌─────────────┐    │
│               │ PreToolUse.py  │◄─────┘      │  Stop.py    │    │
│               │ (RECALL)       │             │  (STORE)    │    │
│               └───────┬────────┘             └──────┬──────┘    │
│                       │                             │           │
│                       ▼                             ▼           │
│               ┌─────────────────────────────────────────┐       │
│               │            dana-memory                  │       │
│               │         (vector database)               │       │
│               └─────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **RECALL (PreToolUse)**: Before each tool use, extracts Claude's thinking block, queries for similar memories, injects relevant ones into context
2. **STORE (Stop)**: After Claude's turn, scans response for `[REMEMBER: ...]` patterns and stores them
