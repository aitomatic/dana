# Conversation Memory Specification

## Overview

This specification defines the design, implementation, and integration patterns for conversation memory in the Dana framework. It addresses the current issues with file placement and provides a unified approach for all agent types.

## Current Issues

### 1. Inconsistent File Placement
- **Problem**: Some agents create `conversation_memory.json` in the current working directory
- **Root Cause**: Duplicate `_initialize_conversation_memory()` methods with different implementations
- **Impact**: Files scattered across project directories instead of centralized storage

### 2. Duplicate Implementation Methods
- **Problem**: Both `agent_instance.py` and `implementations.py` have conversation memory initialization
- **Root Cause**: Inheritance hierarchy confusion and method duplication
- **Impact**: Inconsistent behavior depending on which method gets called

## Design Principles

### 1. Single Source of Truth
- Only one implementation of conversation memory initialization
- Clear inheritance hierarchy for agent types
- Consistent file placement across all agent instances

### 2. Centralized Storage
- All conversation memory files stored in `~/.dana/chats/`
- Structured naming convention: `{agent_name}_{session_id}_conversation.json`
- Automatic directory creation and management

### 3. Separation of Concerns
- **Agent Instance**: Basic agent functionality and lifecycle
- **Agent Implementations**: Specialized functionality including memory management
- **Memory Framework**: Pure memory implementation without agent-specific logic

## Architecture

### File Structure
```
~/.dana/
├── chats/                           # Conversation memory storage
│   ├── agent_alpha_001_conversation.json
│   ├── agent_beta_002_conversation.json
│   └── agent_gamma_003_conversation.json
├── config/                          # Agent configurations
├── logs/                           # Agent logs
└── knowledge/                      # Extracted knowledge
```

### Class Hierarchy
```
AgentInstance (base)
├── _conversation_memory: ConversationMemory | None
├── _initialize_conversation_memory() -> None  # Abstract method
└── chat() -> Any

AgentImplementations (mixin)
├── _initialize_conversation_memory() -> None  # Concrete implementation
└── _chat_impl() -> str

ConversationMemory (framework)
├── filepath: Path
├── history: deque
└── save() / load() methods
```

## Implementation Specification

### 1. Agent Instance Base Class

```python
# dana/builtin_types/agent/agent_instance.py

class AgentInstance:
    def __init__(self, **kwargs):
        # ... other initialization ...
        self._conversation_memory = None  # Lazy initialization
    
    def _initialize_conversation_memory(self):
        """Abstract method - must be implemented by subclasses."""
        raise NotImplementedError(
            "Subclasses must implement _initialize_conversation_memory()"
        )
    
    def chat(self, message: str, **kwargs) -> Any:
        """Execute agent chat method."""
        # Ensure conversation memory is initialized
        if self._conversation_memory is None:
            self._initialize_conversation_memory()
        
        # ... rest of chat implementation ...
```

### 2. Agent Implementations Mixin

```python
# dana/builtin_types/agent/implementations.py

class AgentImplementations:
    def _initialize_conversation_memory(self):
        """Initialize conversation memory with proper file placement."""
        if self._conversation_memory is None:
            from pathlib import Path
            from dana.frameworks.memory.conversation_memory import ConversationMemory
            
            # Create memory file path under ~/.dana/chats/
            agent_name = getattr(self.agent_type, "name", "agent")
            session_id = getattr(self, "session_id", "default")
            
            home_dir = Path.home()
            dana_dir = home_dir / ".dana"
            memory_dir = dana_dir / "chats"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Structured naming: {agent_name}_{session_id}_conversation.json
            memory_file = memory_dir / f"{agent_name}_{session_id}_conversation.json"
            
            self._conversation_memory = ConversationMemory(
                filepath=str(memory_file),
                max_turns=20
            )
```

### 3. Conversation Memory Framework

```python
# dana/frameworks/memory/conversation_memory.py

class ConversationMemory:
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
        self.max_turns = max_turns
        # ... rest of implementation ...
```

## Integration Patterns

### 1. Agent Creation Flow
```
1. Create AgentInstance
2. Agent calls _initialize_conversation_memory() (abstract)
3. Subclass implementation creates ConversationMemory with proper filepath
4. Memory file created in ~/.dana/chats/
5. Agent.chat() uses initialized memory
```

### 2. Memory Persistence Flow
```
1. Agent.chat() receives message
2. Message processed and response generated
3. ConversationMemory.add_turn() called
4. Turn saved to memory and persisted to file
5. File automatically saved to ~/.dana/chats/
```

### 3. Context Building Flow
```
1. Agent needs context for LLM
2. ConversationMemory.get_recent_context() called
3. Recent turns retrieved from memory
4. Context assembled for LLM prompt
5. LLM generates response with context
```

## Configuration

### Environment Variables
```bash
# Dana home directory (default: ~/.dana)
DANA_HOME=~/.dana

# Conversation memory settings
DANA_MEMORY_MAX_TURNS=20
DANA_MEMORY_AUTO_SAVE=true
DANA_MEMORY_COMPRESSION=false
```

### Agent Configuration
```python
agent_config = {
    "memory": {
        "max_turns": 20,
        "auto_save": True,
        "compression": False,
        "custom_filepath": None  # Override default ~/.dana/chats/ location
    }
}
```

## Migration Strategy

### Phase 1: Remove Duplicate Methods
1. Remove `_initialize_conversation_memory()` from `agent_instance.py`
2. Ensure all agents inherit from `AgentImplementations` mixin
3. Update tests to use proper inheritance

### Phase 2: File Organization
1. Move existing `conversation_memory.json` files to `~/.dana/chats/`
2. Update file naming to follow convention
3. Clean up scattered memory files

### Phase 3: Validation
1. Verify all agents use centralized storage
2. Test memory persistence across agent types
3. Validate file cleanup and lifecycle management

## Testing Requirements

### Unit Tests
- Test conversation memory initialization
- Test file placement in `~/.dana/chats/`
- Test memory persistence and loading
- Test context building for LLM

### Integration Tests
- Test agent.chat() with memory
- Test memory across different agent types
- Test file cleanup on agent destruction
- Test concurrent agent memory isolation

### Performance Tests
- Test memory operations with large conversation histories
- Test file I/O performance
- Test memory cleanup and garbage collection

## Future Enhancements

### 1. Memory Compression
- Automatic summarization of old conversations
- Vector-based similarity search
- Semantic clustering of conversation topics

### 2. Multi-Agent Memory
- Shared memory pools for agent teams
- Cross-agent conversation context
- Memory synchronization and conflict resolution

### 3. Advanced Persistence
- Database backend for large-scale deployments
- Memory encryption and security
- Backup and recovery mechanisms

## Compliance Requirements

### 1. File System
- All memory files must be stored in `~/.dana/chats/`
- No memory files in project directories
- Proper file permissions and security

### 2. Agent Lifecycle
- Memory initialization on first use
- Proper cleanup on agent destruction
- Session isolation between agent instances

### 3. Error Handling
- Graceful fallback when memory operations fail
- Clear error messages for debugging
- Automatic recovery from corrupted memory files

## Conclusion

This specification provides a clear path to resolve the current conversation memory issues while establishing a robust foundation for future enhancements. The key is eliminating duplicate implementations and ensuring consistent file placement across all agent types.
