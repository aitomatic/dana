# Dana Hook Adapters

Hook adapters that integrate `dana-memory` with various AI agent systems.

## Claude Code

### Installation

```bash
# Copy the hook to Claude's hooks directory
mkdir -p ~/.claude/hooks
cp claude/PreToolUse.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/PreToolUse.py
```

### Configuration

Set environment variables to customize behavior:

```bash
# In your shell profile (~/.zshrc, ~/.bashrc, etc.)
export DANA_MEMORY_ENABLED=1        # Enable memory injection (default: 1)
export DANA_MEMORY_MIN_SCORE=0.3    # Minimum relevance score (default: 0.3)
export DANA_MEMORY_LIMIT=3          # Max memories to inject (default: 3)
export DANA_MEMORY_DOMAIN=hvac      # Filter by domain (default: all)
export DANA_MEMORY_SKIP_TOOLS=Glob,Grep,Bash  # Tools to skip (default)
```

### How It Works

1. Before Claude uses a tool, the hook fires
2. Hook extracts the last thinking block (Claude's reasoning)
3. Hook queries `dana-memory` with that context
4. Relevant memories are injected into Claude's context
5. Claude sees the memories before executing the tool

```
User Prompt → Claude thinks → PreToolUse hook fires
                                     ↓
                              Extract thinking block
                                     ↓
                              Query dana-memory
                                     ↓
                              Inject relevant memories
                                     ↓
                              Tool executes with context
```

### Skipped Tools

By default, these tools are skipped (no memory lookup):
- `Glob` — Simple file pattern matching
- `Grep` — Simple text search
- `Bash` — Too frequent, often simple commands
- `TaskList`, `TaskGet` — Task management

Configure with `DANA_MEMORY_SKIP_TOOLS`.

## Other Agent Systems

### Generic Integration

Any agent system that can call shell commands can use `dana-memory`:

```bash
# Query before making decisions
memories=$(dana-memory query "current task context" --json)

# Store learnings
dana-memory store "what was learned" --domain domain --source agent
```

### Python Integration

```python
from dana.lib.memory import MemoryStore

store = MemoryStore()

# Before tool execution
memories = store.query(current_context, limit=3, min_score=0.3)
for m in memories:
    inject_into_context(m.text)

# After learning something
store.store("learned pattern", domain="agent", source="session")
```

## Creating New Adapters

To create an adapter for a new agent system:

1. Create a new directory: `hooks/{system}/`
2. Implement the hook in the system's required format
3. The hook should:
   - Extract current context/reasoning
   - Call `dana-memory query` or use the Python API
   - Inject relevant memories into the agent's context
4. Add installation instructions to this README
