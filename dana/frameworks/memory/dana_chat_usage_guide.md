# Using Agent Chat in Dana Language

## Overview

The `agent.chat()` method in Dana provides conversational AI capabilities with automatic memory management. It allows agents to engage in natural conversations while remembering context across sessions.

## Basic Usage

### 1. Define an Agent

```dana
# Define a conversational agent
agent ChatAssistant:
    name: str = "Assistant"
    personality: str = "friendly and helpful"
    expertise: str = "general assistance and problem solving"
    language: str = "English"
```

### 2. Create an Instance and Chat

```dana
# Create an instance
assistant = ChatAssistant()

# Start chatting
response = assistant.chat("Hello! My name is Alice.")
print(f"Assistant: {response}")

# Continue the conversation
response = assistant.chat("What can you help me with?")
print(f"Assistant: {response}")

# Test memory
response = assistant.chat("Do you remember my name?")
print(f"Assistant: {response}")
```

## Advanced Usage

### 1. Chat with Custom Context

```dana
# Chat with additional context
response = assistant.chat(
    "How should I start learning Python?",
    context={
        "topic": "Python programming",
        "level": "beginner",
        "goal": "web development"
    },
    max_context_turns=3  # Only include last 3 turns
)
```

### 2. Multiple Agents with Separate Memories

```dana
# Create different types of agents
agent SupportAgent:
    department: str = "technical"
    expertise: str = "technical support"

agent SalesAgent:
    region: str = "north"
    expertise: str = "product sales"

# Create instances
support = SupportAgent()
sales = SalesAgent()

# Each maintains separate conversation history
support.chat("I have a technical issue")
sales.chat("I'm interested in your products")

# Conversations are completely separate
support.chat("What products do you sell?")  # Won't know about sales conversation
sales.chat("Can you fix my computer?")      # Won't know about support conversation
```

### 3. Agent with LLM Integration

```dana
# If you have an LLM configured, add it to the agent's context
from dana import llm

assistant._context['llm'] = llm

# Now chat will use the LLM for better responses
response = assistant.chat("Explain quantum computing to me")
```

## Memory Management

### 1. Check Conversation Statistics

```dana
# Get conversation statistics
stats = assistant.get_conversation_stats()
print(f"Total turns: {stats['total_turns']}")
print(f"Active turns: {stats['active_turns']}")
print(f"Session count: {stats['session_count']}")
```

### 2. Clear Conversation Memory

```dana
# Clear all conversation history
assistant.clear_conversation_memory()
```

### 3. Memory Persistence

Conversations are automatically saved to:
- `agent_memories/{AgentName}_conversation.json`
- Persists across sessions and restarts
- Each agent type has its own memory file

## Complete Example

```dana
# Complete conversational agent example
agent PersonalAssistant:
    name: str = "Dana Assistant"
    personality: str = "helpful and knowledgeable"
    expertise: str = "general assistance, programming, and problem solving"
    preferred_language: str = "English"

# Create the assistant
assistant = PersonalAssistant()

print("=== Chat with Personal Assistant ===\n")

# Initial conversation
response1 = assistant.chat("Hi! I'm new to programming.")
print(f"User: Hi! I'm new to programming.")
print(f"Assistant: {response1}\n")

# Ask for help
response2 = assistant.chat("What programming language should I learn first?")
print(f"User: What programming language should I learn first?")
print(f"Assistant: {response2}\n")

# Test memory
response3 = assistant.chat("What did I tell you about myself?")
print(f"User: What did I tell you about myself?")
print(f"Assistant: {response3}\n")

# Use other agent capabilities
plan = assistant.plan("Help user learn Python programming")
print(f"\nPlan: {plan}")

# Store information in memory
assistant.remember("user_goal", "learn Python programming")
goal = assistant.recall("user_goal")
print(f"\nRemembered goal: {goal}")

# Advanced chat with context
response4 = assistant.chat(
    "How should I start?",
    context={"topic": "Python", "level": "beginner"},
    max_context_turns=2
)
print(f"\nUser: How should I start?")
print(f"Assistant: {response4}")

# Show conversation statistics
stats = assistant.get_conversation_stats()
print(f"\n=== Conversation Statistics ===")
print(f"Total turns: {stats['total_turns']}")
print(f"Active turns: {stats['active_turns']}")
print(f"Session count: {stats['session_count']}")
```

## Method Parameters

### `chat(message, context=None, max_context_turns=5)`

- **`message`** (str): The user's message
- **`context`** (dict, optional): Additional context for the conversation
- **`max_context_turns`** (int, default=5): Maximum number of recent turns to include in context

## Built-in Fallback Responses

When no LLM is available, the chat method provides intelligent fallback responses:

- **Greetings**: "Hello! I'm {agent_name}. How can I help you today?"
- **Name queries**: "I'm {agent_name}, an AI agent. How can I assist you?"
- **Memory queries**: Searches conversation history for relevant topics
- **Help queries**: Explains agent capabilities

## Best Practices

### 1. Use Descriptive Agent Names

```dana
# ✅ Good
agent TechnicalSupportAgent:
    department: str = "technical"
    expertise: str = "software troubleshooting"

# ❌ Avoid
agent Agent:
    field1: str = "value"
```

### 2. Provide Relevant Context

```dana
# ✅ Good - provides useful context
response = assistant.chat(
    "Help me debug this code",
    context={
        "language": "Python",
        "error_type": "syntax error",
        "experience_level": "intermediate"
    }
)

# ❌ Avoid - no context
response = assistant.chat("Help me debug this code")
```

### 3. Manage Memory Appropriately

```dana
# ✅ Good - clear memory when starting new topics
assistant.clear_conversation_memory()
assistant.chat("Let's start a new conversation about machine learning")

# ✅ Good - use meaningful context limits
assistant.chat("Continue our discussion", max_context_turns=10)
```

### 4. Combine with Other Agent Methods

```dana
# Use chat for conversation, other methods for specific tasks
conversation = assistant.chat("I need help with data analysis")
plan = assistant.plan("Analyze customer data")
solution = assistant.solve("High customer churn rate")

# Store important information
assistant.remember("analysis_goal", "reduce customer churn")
```

## Integration with Dana's Type System

```dana
# Agents can be used in function signatures
def process_conversation(agent: PersonalAssistant, message: str) -> str:
    return agent.chat(message)

# Agents can be used in structs
struct ConversationSession:
    agent: PersonalAssistant
    start_time: str
    messages: list[str]

# Agents can be used in collections
agents = [
    PersonalAssistant(name="Assistant 1"),
    PersonalAssistant(name="Assistant 2")
]

for agent in agents:
    response = agent.chat("Hello!")
```

## Error Handling

The chat method handles errors gracefully:

```dana
# If LLM fails, falls back to basic responses
try:
    response = assistant.chat("Complex question requiring LLM")
except Exception as e:
    print(f"LLM error: {e}")
    # Method will still provide fallback response
```

## Summary

The `agent.chat()` method provides:
- **Automatic Memory Management**: Remembers conversations across sessions
- **Context Building**: Builds rich context for LLM prompts
- **LLM Integration**: Uses LLM when available, falls back gracefully
- **Persistence**: Saves conversations to JSON files
- **Type Safety**: Full Dana type system integration
- **Easy to Use**: Simple API for conversational AI

Perfect for: Chatbots, virtual assistants, customer service agents, and any application requiring conversational AI with memory. 