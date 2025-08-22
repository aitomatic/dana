# Conversation Memory Implementation Plan

## Overview

This document outlines the phased implementation approach for a conversation memory system that enables agents to remember and recall conversation history with humans. The system starts with a simple JSON-based approach and evolves toward more sophisticated features.

## Goals

1. **Primary Goal**: Enable an agent to conduct conversations with humans and remember what was said
2. **Efficient Recall**: Retrieve relevant context without loading everything into the context window
3. **Persistence**: Maintain conversation history across sessions
4. **Scalability Path**: Design allows evolution to more sophisticated approaches

## Implementation Approach

### Phase 1: Simple Linear Memory with JSON Persistence (Current)
**Timeline**: Week 1
**Status**: Starting

#### Objectives
- Implement basic ConversationMemory class with deque-based history
- JSON file persistence for conversation data
- Simple context assembly for LLM prompts
- Basic turn management (add, retrieve)

#### Key Components
1. **ConversationMemory Class**
   - Linear history using collections.deque
   - Configurable max history depth (default 20 turns)
   - JSON serialization/deserialization
   - Auto-save on updates

2. **Storage Format**
   ```json
   {
     "conversation_id": "uuid",
     "created_at": "2024-01-20T10:00:00Z",
     "updated_at": "2024-01-20T11:30:00Z",
     "history": [
       {
         "turn_id": "uuid",
         "user_input": "Hello, how are you?",
         "agent_response": "I'm doing well, thank you!",
         "timestamp": "2024-01-20T10:00:00Z",
         "metadata": {}
       }
     ],
     "summaries": [],
     "metadata": {
       "user_id": "optional",
       "session_count": 1
     }
   }
   ```

3. **Core Methods**
   - `add_turn(user_input, agent_response)` - Add conversation turn
   - `get_recent_context(n_turns=5)` - Get recent turns
   - `build_llm_context(current_query)` - Assemble context for LLM
   - `save()` / `load()` - Persistence operations

#### Success Criteria
- [ ] Can maintain conversation history up to 20 turns
- [ ] History persists across restarts
- [ ] Context assembly works for LLM prompts
- [ ] JSON files are human-readable

### Phase 2: Add Summarization
**Timeline**: Week 2
**Status**: Planned

#### Objectives
- Implement automatic summarization of older conversations
- Reduce context size while preserving important information
- Support both rule-based and LLM-based summarization

#### Key Features
- Summarize every 10-20 turns
- Store summaries separately from raw history
- Include summaries in context assembly
- Configurable summarization triggers

#### Implementation
1. **Rule-based Summarization**
   - Extract key topics/entities
   - Identify important exchanges
   - Format as bullet points

2. **LLM-based Summarization** (if available)
   - Use LLM to create concise summaries
   - Preserve key facts and context
   - Maintain conversation flow

### Phase 3: Semantic Memory with Vector Search
**Timeline**: Weeks 3-4
**Status**: Future

#### Objectives
- Add semantic search capabilities
- Retrieve relevant past conversations based on similarity
- Implement embeddings for conversation turns

#### Key Features
- Sentence transformer embeddings
- Local vector storage (FAISS)
- Hybrid retrieval (recent + relevant)
- Similarity-based context assembly

#### Components
1. **Embedding Generation**
   - Embed user inputs and responses
   - Store embeddings alongside turns
   - Batch processing for efficiency

2. **Vector Search**
   - FAISS index for similarity search
   - Configurable similarity threshold
   - Return relevant historical context

### Phase 4: Integration with KNOWS
**Timeline**: Weeks 5-6
**Status**: Future

#### Objectives
- Extract knowledge from conversations
- Feed conversation insights to KNOWS system
- Use KNOWS knowledge to enhance responses

#### Features
- Automatic knowledge extraction from conversations
- Categorize extracted knowledge (factual, procedural, etc.)
- Bi-directional integration with KNOWS
- Knowledge-enhanced context assembly

## Technical Architecture

### Dependencies
- Python 3.x standard library (json, uuid, datetime, collections)
- No external dependencies for Phase 1
- Future: sentence-transformers, faiss-cpu (Phase 3)

### File Structure
```
dana/frameworks/memory/
├── __init__.py
├── conversation_memory.py      # Core memory class
├── context_builder.py         # Context assembly logic
├── summarizer.py             # Summarization logic (Phase 2)
├── vector_memory.py          # Semantic search (Phase 3)
├── knows_integration.py      # KNOWS integration (Phase 4)
└── tests/
    ├── test_conversation_memory.py
    ├── test_context_builder.py
    └── test_scenarios.py
```

### Error Handling
- Graceful handling of missing/corrupt JSON files
- Automatic backup before updates
- Validation of conversation data
- Clear error messages

### Performance Considerations
- Lazy loading of conversation history
- Incremental saves (append-only where possible)
- Configurable memory limits
- Efficient context assembly

## Usage Example

```python
from dana.frameworks.memory import ConversationMemory

# Initialize memory
memory = ConversationMemory(filepath="agent_memory.json", max_turns=20)

# Add a conversation turn
memory.add_turn(
    user_input="What's the weather like today?",
    agent_response="I don't have access to current weather data, but I can help you with other questions."
)

# Get context for LLM
context = memory.build_llm_context(
    current_query="Can you remember what we talked about?"
)

# Context will include recent conversation history
print(context)
```

## Testing Strategy

### Unit Tests
- Test all core methods
- Verify persistence/loading
- Test edge cases (empty history, max capacity)
- Validate JSON serialization

### Integration Tests
- Full conversation scenarios
- Multi-turn conversations
- Persistence across sessions
- Context assembly validation

### Test Scenarios
1. **Basic Conversation**: Simple back-and-forth
2. **Long Conversation**: Exceeding max_turns limit
3. **Multi-topic**: Switching between topics
4. **Recall Test**: Asking about previous discussions
5. **Persistence Test**: Restart and continue conversation

## Success Metrics

### Phase 1 Metrics
- Memory retrieval time: < 10ms
- Context assembly time: < 50ms
- JSON file size: < 1MB for 1000 turns
- Zero data loss on save/load

### Overall Success Criteria
- Agent can accurately recall conversation history
- Context stays within LLM token limits
- Performance remains good with long conversations
- Easy to debug and maintain

## Risk Mitigation

### Identified Risks
1. **File Corruption**: Mitigated by atomic writes and backups
2. **Memory Growth**: Mitigated by turn limits and summarization
3. **Performance**: Mitigated by lazy loading and caching
4. **Concurrency**: Phase 1 assumes single-user; will address in future phases

## Progress Tracking

### Phase 1 Progress
- [x] Create project structure
- [x] Implement ConversationMemory class
- [x] Add JSON persistence
- [x] Implement context assembly
- [x] Create unit tests
- [x] Create integration tests
- [x] Documentation
- [ ] Initial deployment

### Completed Milestones
- [x] Review memory/knowledge framework specifications
- [x] Design implementation plan
- [x] Choose JSON-based approach for simplicity

## Next Steps

1. Create the project structure
2. Implement the basic ConversationMemory class
3. Add JSON persistence functionality
4. Create test scenarios
5. Iterate based on testing feedback

## Notes

- Starting simple with JSON allows quick iteration and learning
- The design supports evolution to more sophisticated approaches
- Each phase builds on the previous one
- User feedback will guide feature prioritization