# Dana Memory Framework

The Dana Memory Framework provides conversation memory capabilities for Dana agents, enabling them to remember and recall past interactions with users.

## Features

- **Conversation Memory**: Agents can remember conversation history across sessions
- **Context Building**: Automatically builds context from recent conversations for LLM interactions
- **JSON Persistence**: Conversations are saved to JSON files for easy debugging and portability
- **Multi-Agent Support**: Each agent maintains its own separate conversation memory
- **Configurable History**: Set maximum turns to keep in active memory
- **Search Capability**: Search through conversation history
- **Statistics**: Track conversation metrics and session counts

## Quick Start

### Using Chat in Dana Agents

All Dana agents now have a built-in `.chat()` method:

```dana
# Define an agent
agent CustomerSupport:
    name = "Support Bot"
    department = "Technical Support"

# Create instance
support = CustomerSupport()

# Chat with the agent
response = support.chat("Hello, I need help with my computer")
print(response)

# The agent remembers the conversation
response = support.chat("It won't turn on")
print(response)

# Check what was discussed
response = support.chat("What did I tell you about?")
print(response)
```

### Conversation Memory Location

Conversations are automatically saved to your Dana configuration directory:
```
~/.dana/chats/<AgentName>_conversation.json
```

The `.dana` directory structure:
```
~/.dana/
└── chats/
    ├── SupportAgent_conversation.json
    ├── AssistantBot_conversation.json
    └── CustomAgent_conversation.json
```

Each agent maintains its own conversation file, allowing for:
- **Isolated conversations** - Each agent type has separate memory
- **Persistent sessions** - Conversations survive application restarts  
- **Easy management** - Simple JSON files for debugging and backup

### Advanced Usage

```dana
# Chat with additional context
response = agent.chat(
    "Help me with this",
    context={"priority": "high", "category": "billing"},
    max_context_turns=10  # Include more history
)

# Access conversation statistics
stats = agent.get_conversation_stats()
print(f"Total turns: {stats['total_turns']}")

# Clear conversation history
agent.clear_conversation_memory()
```

### Using with LLM

**Automatic LLM Integration (Recommended):**

Agents automatically use Dana's LLMResource when available. Just configure your API keys:

```bash
# Set environment variables
export OPENAI_API_KEY="your-key-here"
# or ANTHROPIC_API_KEY, GROQ_API_KEY, etc.

# Or configure in dana_config.json
```

```dana
agent CustomerSupport:
    name = "Support Bot"

support = CustomerSupport()

# Automatically uses LLM if configured, falls back to simple responses if not
response = support.chat("Explain quantum computing simply")
```

**Manual LLM Assignment:**

You can also manually provide an LLM function:

```dana
# Add custom LLM to agent's context
agent._context['llm'] = your_custom_llm_function

# Or set as agent field
agent MyAgent:
    llm = your_llm_function

# Now chat responses will use the specified LLM
response = agent.chat("Explain quantum computing")
```

## Implementation Details

### ConversationMemory Class

The core memory system is implemented in `conversation_memory.py`:

```python
from dana.frameworks.memory import ConversationMemory

# Create a memory instance
memory = ConversationMemory(filepath="my_memory.json", max_turns=20)

# Add a conversation turn
memory.add_turn(
    user_input="What's the weather?",
    agent_response="I don't have weather data access."
)

# Build context for LLM
context = memory.build_llm_context("Tell me more about weather")

# Search history
results = memory.search_history("weather")

# Get statistics
stats = memory.get_statistics()
```

### Memory Features

1. **Linear History**: Uses Python's `deque` for efficient turn management
2. **Automatic Persistence**: Saves after each turn
3. **Atomic Writes**: Prevents corruption with temp file + rename
4. **Backup System**: Creates `.bak` files before saves
5. **Session Tracking**: Counts how many times the conversation has been loaded

### Context Assembly

The system builds context for LLM prompts by combining:
- Recent conversation turns (configurable)
- Conversation summaries (future feature)
- Current user query
- Optional additional context

## Architecture

```
dana/frameworks/memory/
├── __init__.py                 # Package initialization
├── conversation_memory.py      # Core memory implementation
├── implementation_plan.md      # Detailed implementation plan
├── README.md                   # This file
└── examples/
    ├── chat_agent_example.na   # Dana agent example
    └── example_usage.py        # Python usage examples

dana/agent/
└── agent_struct_system.py      # Agent system with integrated chat methods
```

## Future Enhancements

### Phase 2: Summarization
- Automatic summarization of older conversations
- LLM-based summary generation
- Compression of conversation history

### Phase 3: Semantic Search
- Vector embeddings for conversation turns
- Similarity-based retrieval
- Hybrid search (recent + relevant)

### Phase 4: Knowledge Integration
- Extract facts from conversations
- Integration with KNOWS framework
- Bi-directional knowledge flow

## Testing

Run the test suite:

```bash
# Test conversation memory
python -m dana.frameworks.memory.test_conversation_memory

# Test agent chat integration
python -m dana.frameworks.memory.test_agent_chat

# Run example usage
python -m dana.frameworks.memory.example_usage
```

## Performance

- Memory retrieval: < 10ms
- Context assembly: < 50ms
- JSON file size: ~1KB per 10 turns
- Max recommended turns: 10,000 per conversation

## Contributing

When adding new features:
1. Update `conversation_memory.py` for core functionality
2. Update `agent_chat_extension.py` for agent integration
3. Add tests to the test suite
4. Update this README

## License

Part of the Dana Language Project