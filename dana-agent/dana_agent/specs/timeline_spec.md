# Timeline System Specification

## Overview

The Timeline system provides a unified, chronological record of all agent interactions, enabling efficient context management and preventing context window explosion in multi-agent environments. This replaces the current per-correspondent conversation history approach with a single, comprehensive timeline.

## Core Concepts

### TimelineEntry
A single entry in an agent's timeline representing one interaction or event.

**Properties:**
- `timestamp`: When the interaction occurred
- `entry_type`: Type of interaction (user_input, my_response, agent_interaction, resource_call)
- `content`: The actual content/message
- `correspondent`: Who the interaction was with (optional)
- `metadata`: Additional context information

### TimelineManager
Manages the timeline for an agent, handling context building and token management.

**Responsibilities:**
- Add new timeline entries
- Build context within token limits
- Estimate token usage
- Provide timeline queries and filtering

### Timeline Types
Different types of timeline entries for various interaction patterns:

1. **user_input**: Input from human users
2. **my_response**: Agent's responses to users
3. **agent_interaction**: Communication with other agents
4. **resource_call**: Calls to external resources/APIs
5. **system_event**: Internal system events
6. **error_event**: Error occurrences and handling

## Design Principles

1. **Single Source of Truth**: One timeline per agent containing all interactions
2. **Chronological Order**: Natural conversation flow maintained
3. **Context Management**: Token-aware context building prevents window explosion
4. **Rich Metadata**: Track who, what, when, where for debugging and analysis
5. **Scalable**: Works with any number of agents and resources
6. **Efficient**: Minimal overhead for timeline operations

## TimelineEntry Specification

```python
@dataclass
class TimelineEntry:
    timestamp: datetime
    entry_type: str
    content: str
    correspondent: str | None = None
    metadata: dict = field(default_factory=dict)
    
    def to_llm_message(self) -> LLMMessage:
        """Convert to LLM message format for context building."""
        pass
    
    def to_string(self) -> str:
        """Convert to human-readable string format."""
        pass
    
    def is_user_interaction(self) -> bool:
        """Check if this is a user interaction."""
        pass
    
    def is_agent_interaction(self) -> bool:
        """Check if this is an agent interaction."""
        pass
    
    def is_resource_call(self) -> bool:
        """Check if this is a resource call."""
        pass
```

## TimelineManager Specification

```python
class TimelineManager:
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

## Agent Integration

### Updated Agent Class
```python
class Agent:
    def __init__(self, agent_id: str, max_context_tokens: int = 4000):
        self.agent_id = agent_id
        self.timeline_manager = TimelineManager(max_context_tokens)
        self.llm = LLM()
    
    async def chat(self, user_input: str) -> str:
        """Chat with timeline-based context management."""
        # Add user input to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="user_input",
            content=user_input
        ))
        
        # Build context from timeline
        messages = self.timeline_manager.get_context()
        
        # Get LLM response
        response = await self.llm.chat(messages)
        
        # Add response to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="my_response",
            content=response
        ))
        
        return response
    
    async def interact_with_agent(self, other_agent_id: str, message: str) -> str:
        """Interact with another agent."""
        # Add outgoing message to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="agent_interaction",
            content=message,
            correspondent=other_agent_id
        ))
        
        # Process interaction...
        
        # Add response to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="agent_interaction",
            content=response,
            correspondent=other_agent_id
        ))
        
        return response
    
    async def call_resource(self, resource_id: str, request: str) -> str:
        """Call external resource."""
        # Add resource call to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="resource_call",
            content=request,
            correspondent=resource_id
        ))
        
        # Process resource call...
        
        # Add response to timeline
        self.timeline_manager.add_entry(TimelineEntry(
            timestamp=datetime.now(),
            entry_type="resource_call",
            content=response,
            correspondent=resource_id
        ))
        
        return response
```

## Context Management Strategies

### 1. Sliding Window
Keep only the last N entries in context.

### 2. Token-Based Truncation
Keep entries within token limits, prioritizing recent entries.

### 3. Summarization
Summarize old entries to save tokens while maintaining context.

### 4. Hybrid Approach
Combine sliding window with token limits for optimal performance.

## Timeline Examples

### Basic User Conversation
```
[2024-01-15 10:00:00] [User] Hello, how are you?
[2024-01-15 10:00:01] [Me] I'm doing well, thank you! How can I help you today?
[2024-01-15 10:00:05] [User] What's the weather like?
[2024-01-15 10:00:06] [Me] I'll check the weather for you.
[2024-01-15 10:00:07] [Me-to-WeatherAPI] GET /weather?location=current
[2024-01-15 10:00:08] [WeatherAPI] Temperature: 72°F, Sunny
[2024-01-15 10:00:09] [Me] It's 72°F and sunny where you are!
```

### Multi-Agent Interaction
```
[2024-01-15 10:00:00] [User] Help me write a Python function
[2024-01-15 10:00:01] [Me] I'll help you with that. Let me ask our coding specialist.
[2024-01-15 10:00:02] [Me-to-CodingAgent] User needs help with Python function
[2024-01-15 10:00:03] [CodingAgent] What kind of function do you need?
[2024-01-15 10:00:04] [Me] What kind of function do you need?
[2024-01-15 10:00:05] [User] A function to calculate fibonacci numbers
[2024-01-15 10:00:06] [Me-to-CodingAgent] User wants fibonacci function
[2024-01-15 10:00:07] [CodingAgent] Here's a fibonacci function: def fib(n): ...
[2024-01-15 10:00:08] [Me] Here's a fibonacci function: def fib(n): ...
```

## Testing Strategy

### Unit Tests
- TimelineEntry creation and properties
- TimelineManager operations
- Token estimation accuracy
- Context building logic

### Integration Tests
- Agent-timeline integration
- Multi-agent timeline interactions
- Resource call timeline tracking

### Functional Tests
- End-to-end conversation flows
- Long conversation context management
- Performance under load

### Performance Tests
- Token limit enforcement
- Memory usage patterns
- Timeline operation speed

## Migration Plan

### Phase 1: Core Implementation
- Implement TimelineEntry and TimelineManager
- Update Agent class to use timeline
- Create comprehensive tests

### Phase 2: Integration
- Update examples to use timeline
- Test with existing LLM providers
- Validate performance

### Phase 3: Migration
- Provide migration utilities
- Update documentation
- Gradual rollout

### Phase 4: Cleanup
- Remove old conversation history code
- Optimize timeline operations
- Final validation

## Benefits

1. **Context Window Management**: Prevents explosion in multi-agent environments
2. **Unified History**: Single source of truth for all interactions
3. **Rich Debugging**: Complete audit trail of agent behavior
4. **Scalable**: Works with any number of agents and resources
5. **Efficient**: Token-aware context building
6. **Flexible**: Multiple context management strategies

## Future Enhancements

1. **Timeline Persistence**: Save/load timelines from storage
2. **Timeline Analytics**: Analyze interaction patterns
3. **Timeline Sharing**: Share timeline segments between agents
4. **Timeline Compression**: Advanced summarization techniques
5. **Timeline Search**: Query timeline entries by content or metadata
