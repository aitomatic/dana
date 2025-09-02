# Conversation Memory Migration Plan

## Immediate Actions Required

This document outlines the specific steps needed to resolve the current conversation memory issues and implement the new specification.

## Current State Analysis

### Files with Issues
1. **`dana/builtin_types/agent/agent_instance.py`** (line 585)
   - Has duplicate `_initialize_conversation_memory()` method
   - Creates `conversation_memory.json` in current directory
   - **Action**: Remove this method entirely

2. **`dana/builtin_types/agent/implementations.py`** (lines 131-155)
   - Has correct implementation using `~/.dana/chats/`
   - **Action**: Keep this implementation, ensure all agents use it

### Inheritance Issues
- Some agents may not be properly inheriting from `AgentImplementations` mixin
- This causes the wrong `_initialize_conversation_memory()` method to be called

## Phase 1: Remove Duplicate Methods (Immediate)

### Step 1: Remove Duplicate Method
```python
# In dana/builtin_types/agent/agent_instance.py
# REMOVE this entire method:

def _initialize_conversation_memory(self):
    """Initialize the conversation memory for this agent."""
    self._conversation_memory = ConversationMemory()
```

### Step 2: Make Method Abstract
```python
# In dana/builtin_types/agent/agent_instance.py
# REPLACE with:

def _initialize_conversation_memory(self):
    """Abstract method - must be implemented by subclasses."""
    raise NotImplementedError(
        "Subclasses must implement _initialize_conversation_memory()"
    )
```

### Step 3: Update Import
```python
# In dana/builtin_types/agent/agent_instance.py
# REMOVE this import since it's no longer used directly:

from dana.frameworks.memory.conversation_memory import ConversationMemory
```

## Phase 2: Ensure Proper Inheritance

### Step 1: Verify Agent Class Hierarchy
Check that all agent classes properly inherit from `AgentImplementations`:

```python
# Example correct inheritance:
class MyAgent(AgentInstance, AgentImplementations):
    # ... agent implementation ...
```

### Step 2: Update Agent Base Classes
If any agents don't inherit from `AgentImplementations`, add it:

```python
# Before:
class MyAgent(AgentInstance):
    pass

# After:
class MyAgent(AgentInstance, AgentImplementations):
    pass
```

## Phase 3: Update ConversationMemory Class

### Step 1: Make Filepath Required
```python
# In dana/frameworks/memory/conversation_memory.py
def __init__(self, filepath: str, max_turns: int = 20):
    """
    Initialize conversation memory.
    
    Args:
        filepath: Path to JSON file for persistence (required)
        max_turns: Maximum number of turns to keep in active memory
    """
    if not filepath:
        raise ValueError("filepath is required for ConversationMemory")
    
    self.filepath = Path(filepath)
    # ... rest of implementation ...
```

### Step 2: Remove Default Filepath
```python
# REMOVE the default parameter:
# def __init__(self, filepath: str = "conversation_memory.json", max_turns: int = 20):

# REPLACE with:
def __init__(self, filepath: str, max_turns: int = 20):
```

## Phase 4: File Cleanup

### Step 1: Find Scattered Files
```bash
# Search for conversation_memory.json files in project directories
find . -name "conversation_memory.json" -type f
```

### Step 2: Move Files to Proper Location
```bash
# Create ~/.dana/chats/ directory if it doesn't exist
mkdir -p ~/.dana/chats/

# Move files with proper naming
# Example: move conversation_memory.json to ~/.dana/chats/agent_default_conversation.json
```

### Step 3: Update .gitignore
```gitignore
# Add to .gitignore to prevent future scattered files
conversation_memory.json
*.conversation.json
```

## Phase 5: Testing and Validation

### Step 1: Unit Tests
```bash
# Run existing memory tests
uv run python -m pytest tests/unit/frameworks/memory/ -v

# Run agent tests
uv run python -m pytest tests/unit/builtin_types/agent/ -v
```

### Step 2: Integration Tests
```bash
# Test agent.chat() functionality
uv run python -m pytest tests/integration/ -v
```

### Step 3: Manual Verification
```python
# Test script to verify file placement
from dana.core.agent import AgentInstance
from pathlib import Path

# Create an agent
agent = MyAgent()

# Chat with it
response = agent.chat("Hello")

# Verify file is in ~/.dana/chats/
home_dir = Path.home()
dana_dir = home_dir / ".dana"
chats_dir = dana_dir / "chats"

# Should find conversation memory files here
print(f"Chat files: {list(chats_dir.glob('*.json'))}")
```

## Rollback Plan

If issues arise during migration:

### Step 1: Restore Original Method
```python
# Temporarily restore the original method in agent_instance.py
def _initialize_conversation_memory(self):
    """Initialize the conversation memory for this agent."""
    self._conversation_memory = ConversationMemory()
```

### Step 2: Revert Filepath Changes
```python
# Restore default filepath in ConversationMemory
def __init__(self, filepath: str = "conversation_memory.json", max_turns: int = 20):
```

## Success Criteria

### Phase 1 Complete When:
- [ ] Duplicate method removed from `agent_instance.py`
- [ ] Method made abstract in base class
- [ ] All tests pass

### Phase 2 Complete When:
- [ ] All agents inherit from `AgentImplementations`
- [ ] No `conversation_memory.json` files created in project directories
- [ ] All conversation memory files stored in `~/.dana/chats/`

### Phase 3 Complete When:
- [ ] `ConversationMemory` requires explicit filepath
- [ ] No default filepath fallback
- [ ] Clear error messages for missing filepath

### Phase 4 Complete When:
- [ ] All scattered files moved to `~/.dana/chats/`
- [ ] `.gitignore` updated
- [ ] File naming follows convention

### Phase 5 Complete When:
- [ ] All tests pass
- [ ] Manual verification successful
- [ ] No regression in functionality

## Timeline

- **Phase 1-2**: 1-2 days (immediate fixes)
- **Phase 3**: 1 day (framework updates)
- **Phase 4**: 1 day (file cleanup)
- **Phase 5**: 1-2 days (testing and validation)

**Total Estimated Time**: 4-6 days

## Risk Assessment

### Low Risk
- Removing duplicate methods
- Making filepath required
- File organization

### Medium Risk
- Inheritance changes
- Test updates
- Integration testing

### Mitigation
- Incremental changes
- Comprehensive testing
- Rollback plan ready
- Clear success criteria

## Next Steps

1. **Immediate**: Remove duplicate method from `agent_instance.py`
2. **This Week**: Update `ConversationMemory` class
3. **Next Week**: File cleanup and testing
4. **Following Week**: Validation and documentation updates
