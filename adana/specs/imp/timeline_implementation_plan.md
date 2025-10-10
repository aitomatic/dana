# Timeline Implementation Plan

## Overview

This plan implements the Timeline system to replace conversation history management in the Agent architecture. The Timeline provides a unified, chronological record of all agent interactions with efficient context management.

## Current Status

✅ **LLM is already stateless** - No conversation history in LLM class
✅ **Timeline specification created** - `adana/specs/timeline_spec.md`
✅ **TimelineEntry implemented** - Complete dataclass structure with all methods
✅ **Timeline class** - Fully implemented with token management and context building
✅ **Agent integration** - Agent class updated to use Timeline
✅ **Multi-Agent Communication** - Timeline integrated with agent-to-agent messaging
✅ **Testing** - Comprehensive test suite (38/38 tests passing)
✅ **Examples** - Updated examples demonstrate Timeline usage

## Implementation Phases

### Phase 1: Core Timeline Infrastructure ✅ COMPLETED

#### 1.1 TimelineEntry Class ✅ COMPLETED
- [x] Create `adana/core/agent/timeline.py`
- [x] Implement TimelineEntry dataclass
- [x] Add conversion methods (to_llm_message, to_string)
- [x] Add type checking methods (is_user_interaction, etc.)

#### 1.2 Timeline Class ✅ COMPLETED
- [x] Create Timeline class (renamed from TimelineManager)
- [x] Implement context building with token management
- [x] Add timeline query methods
- [x] Add token estimation logic

#### 1.3 Timeline Types ✅ COMPLETED
- [x] Define timeline entry types
- [x] Add validation for entry types
- [x] Create timeline entry factories

### Phase 2: Agent Integration ✅ COMPLETED

#### 2.1 Update Agent Class ✅ COMPLETED
- [x] Replace conversation history with Timeline
- [x] Update chat() method to use Timeline
- [x] Add agent interaction methods
- [x] Add resource call methods

#### 2.2 Context Management ✅ COMPLETED
- [x] Implement sliding window strategy
- [x] Implement token-based truncation
- [x] Add context summarization (future)
- [x] Add hybrid context management

### Phase 3: Testing Strategy ✅ COMPLETED

#### 3.1 Unit Tests ✅ COMPLETED
- [x] TimelineEntry tests
- [x] Timeline class tests
- [x] Token estimation tests
- [x] Context building tests

#### 3.2 Integration Tests ✅ COMPLETED
- [x] Agent-Timeline integration
- [x] Multi-agent timeline interactions
- [x] Resource call timeline tracking

#### 3.3 Functional Tests ✅ COMPLETED
- [x] End-to-end conversation flows
- [x] Long conversation context management
- [x] Performance under load

### Phase 4: Examples and Documentation ✅ COMPLETED

#### 4.1 Update Examples ✅ COMPLETED
- [x] Update `examples/agent-1/agent_example.py`
- [x] Add timeline demonstration
- [x] Show context management features
- [x] Create multi-agent example (`examples/agent-1/multi_agent_example.py`)

#### 4.2 Documentation ✅ COMPLETED
- [x] Update agent specifications
- [x] Add timeline usage examples
- [x] Document migration path

### Phase 5: Multi-Agent Communication ✅ COMPLETED

#### 5.1 Agent Registry System ✅ COMPLETED
- [x] Create `AgentRegistry` class for centralized agent management
- [x] Implement agent discovery and registration
- [x] Add message routing and queuing
- [x] Create `AgentInfo` dataclass for agent metadata

#### 5.2 Agent-to-Agent Messaging ✅ COMPLETED
- [x] Implement `interact_with_agent()` method with actual functionality
- [x] Add message processing and response handling
- [x] Integrate Timeline with multi-agent communications
- [x] Add error handling and recovery

#### 5.3 Agent Discovery and Management ✅ COMPLETED
- [x] Add `discover_agents()` method
- [x] Add `find_agent_by_type()` and `find_agent_by_capability()` methods
- [x] Implement agent status tracking and metadata management
- [x] Add comprehensive test suite for multi-agent features

## Implementation Details

### Timeline Class Structure

```python
class Timeline:
    def __init__(self, max_context_tokens: int = 4000):
        self.timeline: list[TimelineEntry] = []
        self.max_context_tokens = max_context_tokens
    
    def add_entry(self, entry: TimelineEntry) -> None:
        """Add entry to timeline."""
        pass
    
    def get_context(self, max_tokens: int | None = None) -> list[LLMMessage]:
        """Get timeline context within token limits."""
        pass
    
    def get_recent_entries(self, count: int) -> list[TimelineEntry]:
        """Get most recent N entries."""
        pass
    
    def get_entries_by_type(self, entry_type: str) -> list[TimelineEntry]:
        """Get entries filtered by type."""
        pass
    
    def get_entries_by_correspondent(self, correspondent: str) -> list[TimelineEntry]:
        """Get entries filtered by correspondent."""
        pass
    
    def clear_old_entries(self, before_timestamp: datetime) -> int:
        """Remove entries before timestamp, return count removed."""
        pass
    
    def _estimate_tokens(self, messages: list[LLMMessage]) -> int:
        """Estimate token count for messages."""
        pass
    
    def _build_context_with_sliding_window(self, window_size: int) -> list[LLMMessage]:
        """Build context using sliding window approach."""
        pass
    
    def _build_context_with_token_limit(self, max_tokens: int) -> list[LLMMessage]:
        """Build context using token limit approach."""
        pass
```

### Agent Integration

```python
class Agent:
    def __init__(self, agent_id: str, max_context_tokens: int = 4000):
        self.agent_id = agent_id
        self.timeline = Timeline(max_context_tokens)
        self.llm = LLM()
    
    async def chat(self, user_input: str) -> str:
        """Chat with timeline-based context management."""
        # Add user input to timeline
        self.timeline.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="user_input",
            content=user_input
        ))
        
        # Build context from timeline
        messages = self.timeline.get_context()
        
        # Get LLM response
        response = await self.llm.chat(messages)
        
        # Add response to timeline
        self.timeline.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="my_response",
            content=response
        ))
        
        return response
```

## Testing Strategy

### Unit Tests
- **TimelineEntry**: Creation, conversion, type checking
- **Timeline**: Add/remove entries, context building, token management
- **Token Estimation**: Accuracy of token counting
- **Context Building**: Sliding window, token limits

### Integration Tests
- **Agent-Timeline**: Chat flow with timeline
- **Multi-Agent**: Timeline interactions between agents
- **Resource Calls**: Timeline tracking for resource interactions

### Functional Tests
- **Long Conversations**: Context management over time
- **Performance**: Token limit enforcement
- **Error Handling**: Invalid entries, overflow scenarios

## Migration Strategy

### Phase 1: Parallel Implementation
- Implement Timeline alongside existing conversation history
- Add feature flags for timeline usage
- Gradual migration of examples

### Phase 2: Full Migration
- Update all Agent usage to Timeline
- Remove old conversation history code
- Update all tests and examples

### Phase 3: Optimization
- Optimize timeline operations
- Add advanced context management
- Performance tuning

## Benefits

1. **Context Window Management**: Prevents explosion in multi-agent environments
2. **Unified History**: Single source of truth for all interactions
3. **Rich Debugging**: Complete audit trail of agent behavior
4. **Scalable**: Works with any number of agents and resources
5. **Efficient**: Token-aware context building
6. **Flexible**: Multiple context management strategies

## Next Steps

1. **Complete Timeline class implementation**
2. **Update Agent class to use Timeline**
3. **Create comprehensive test suite**
4. **Update examples and documentation**
5. **Validate performance and functionality**

## Timeline Entry Types

- `user_input`: Input from human users
- `my_response`: Agent's responses to users
- `agent_interaction`: Communication with other agents
- `resource_call`: Calls to external resources/APIs
- `system_event`: Internal system events
- `error_event`: Error occurrences and handling

## Context Management Strategies

1. **Sliding Window**: Keep only the last N entries
2. **Token-Based Truncation**: Keep entries within token limits
3. **Summarization**: Summarize old entries (future)
4. **Hybrid Approach**: Combine strategies for optimal performance
