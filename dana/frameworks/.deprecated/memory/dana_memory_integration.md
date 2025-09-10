# Dana Memory Integration Plan

## Current State

We have implemented a standalone conversation memory system with:
- JSON-based persistence
- Linear conversation history with configurable depth
- Context assembly for LLM interactions
- Basic search and retrieval

However, this is NOT yet integrated into Dana's agent framework.

## Dana's Current Architecture

1. **Database Layer**: Dana uses SQLAlchemy models for conversations and messages
2. **API Services**: REST APIs handle chat requests and conversation management
3. **Agent System**: Agents are Dana structs with capabilities like `plan()` and `solve()`
4. **Chat Flow**:
   - User sends message via API
   - Chat service creates/retrieves conversation from database
   - Agent processes message (currently no memory context)
   - Response saved to database

## Integration Options

### Option 1: Memory Resource (Recommended)
Create a memory resource that agents can use:

```python
# dana/common/resource/conversation_memory_resource.py
from dana.common.sys_resource.base_resource import BaseResource
from dana.frameworks.memory import ConversationMemory

class ConversationMemoryResource(BaseResource):
    """Resource providing conversation memory capabilities to agents."""
    
    def __init__(self, name: str, memory_file: str = None):
        super().__init__(name, "Conversation memory resource")
        self.memory = ConversationMemory(filepath=memory_file or f"{name}_memory.json")
    
    async def add_turn(self, user_input: str, agent_response: str):
        """Add a conversation turn."""
        return self.memory.add_turn(user_input, agent_response)
    
    async def get_context(self, current_query: str, max_turns: int = 5):
        """Get conversation context for LLM."""
        return self.memory.build_llm_context(current_query, max_turns=max_turns)
```

Then in Dana agents:
```dana
agent CustomerSupport:
    memory = ConversationMemoryResource("customer_support")
    
    def respond(query: str) -> str:
        # Get conversation context
        context = memory.get_context(query)
        
        # Use context in LLM call
        response = llm(f"{context}\n\nUser: {query}")
        
        # Save turn to memory
        memory.add_turn(query, response)
        
        return response
```

### Option 2: Memory Mixin for AgentStruct
Extend the agent struct system with memory capabilities:

```python
# dana/agent/memory_mixin.py
class MemoryEnabledAgentMixin:
    """Mixin to add memory capabilities to agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._memory = ConversationMemory(
            filepath=f"{self.__class__.__name__}_memory.json"
        )
    
    def remember_turn(self, user_input: str, response: str):
        """Remember a conversation turn."""
        self._memory.add_turn(user_input, response)
    
    def get_memory_context(self, query: str):
        """Get memory context for current query."""
        return self._memory.build_llm_context(query)
```

### Option 3: Integrate with Database Layer
Sync our memory system with Dana's existing database:

```python
# dana/api/services/memory_sync_service.py
class MemorySyncService:
    """Sync conversation memory with database."""
    
    def sync_from_database(self, conversation_id: int, memory: ConversationMemory):
        """Load conversation from database into memory."""
        messages = db.query(Message).filter_by(conversation_id=conversation_id).all()
        for msg in messages:
            if msg.sender == "user":
                # Find corresponding agent response
                agent_msg = next((m for m in messages if m.sender == "agent" and m.created_at > msg.created_at), None)
                if agent_msg:
                    memory.add_turn(msg.content, agent_msg.content)
    
    def sync_to_database(self, memory: ConversationMemory, conversation_id: int):
        """Save memory turns to database."""
        # Implementation to sync memory back to database
```

## Recommended Approach

1. **Start with Option 1** (Memory Resource) - Least invasive, works with existing architecture
2. **Add database sync later** (Option 3) - For production use with multiple users
3. **Consider mixin approach** (Option 2) - If memory becomes core to all agents

## Implementation Steps

### Phase 1: Create Memory Resource
1. [ ] Create `ConversationMemoryResource` class
2. [ ] Add async wrappers for memory operations
3. [ ] Create example agent using memory resource
4. [ ] Test with Dana REPL

### Phase 2: Integration with Chat Service
1. [ ] Modify chat service to use memory resource
2. [ ] Pass memory context to agent execution
3. [ ] Ensure memory persists across chat sessions
4. [ ] Add conversation_id to memory metadata

### Phase 3: Database Synchronization
1. [ ] Create sync service for database <-> memory
2. [ ] Handle multi-user scenarios
3. [ ] Add memory configuration to agent definitions
4. [ ] Implement memory cleanup/archival

## Usage Example (After Integration)

```dana
# Define an agent with memory
agent MemoryBot:
    name = "MemoryBot"
    memory = ConversationMemoryResource("memorybot")
    
    def chat(message: str) -> str:
        # Get context from memory
        context = memory.get_context(message)
        
        # Generate response with context
        prompt = f"""
        {context}
        
        User: {message}
        Assistant: """
        
        response = llm(prompt)
        
        # Save to memory
        memory.add_turn(message, response)
        
        return response
```

## Benefits of This Approach

1. **Modular**: Memory system remains independent
2. **Compatible**: Works with existing Dana architecture
3. **Flexible**: Can be used by any agent that needs it
4. **Scalable**: Can evolve to use database backend
5. **Simple**: Easy to understand and debug

## Next Steps

1. Implement ConversationMemoryResource
2. Create example memory-enabled agent
3. Test integration with Dana's chat system
4. Document usage patterns
5. Consider performance optimizations