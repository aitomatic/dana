# Conversation Memory Framework

## Overview

The Conversation Memory Framework provides linear conversation history with summaries for context engineering in LLM interactions.

## Design Goals

- **KISS (Keep It Simple, Stupid)** - Simple linear history with depth limits
- **Context Engineering** - Task-specific context assembly for LLMs
- **Memory Efficiency** - Automatic summarization of older conversations
- **Transparency** - Clear, predictable memory behavior

## Core Components

### **ConversationMemory**

```python
class ConversationMemory:
    def __init__(self, max_history_depth=20):
        self.max_history_depth = max_history_depth
        self.conversation_history = deque(maxlen=max_history_depth)
        self.summaries = []  # Periodic summaries of older conversations
```

### **Memory Operations**

- **`add_turn(user_input, agent_response, timestamp=None)`** - Add conversation turn
- **`get_recent_context(turns=5)`** - Get recent conversation context
- **`build_llm_context(current_query, task_type=None)`** - Build context for LLM
- **`create_summary()`** - Create summary of conversation history

## Context Engineering

### **Task-Specific Context Assembly**

Different tasks benefit from different context assemblies:

- **Conversation** - Recent turns + conversation summaries
- **Problem Solving** - Problem context + relevant knowledge + conversation history
- **Learning** - Learning objectives + progress + conversation history
- **Analysis** - Data context + analysis goals + conversation history

### **Context Building**

```python
def build_llm_context(self, current_query: str, task_type: str = None) -> str:
    """Build context string for LLM prompt engineering."""
    
    context_parts = []
    
    # 1. Recent conversation (immediate context)
    recent_turns = self.get_recent_context(5)
    if recent_turns:
        context_parts.append("Recent conversation:")
        for turn in recent_turns:
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"Agent: {turn['agent']}")
    
    # 2. Conversation summaries (long-term context)
    if self.summaries:
        context_parts.append("Conversation summary:")
        context_parts.append("; ".join(self.summaries))
    
    # 3. Task-specific context
    if task_type:
        context_parts.append(f"Task type: {task_type}")
    
    # 4. Current query
    context_parts.append(f"Current query: {current_query}")
    
    return "\n\n".join(context_parts)
```

## Integration with Knowledge Bases

### **Memory vs Knowledge**

- **Memory**: Experiential, contextual, conversation-specific
- **Knowledge**: Factual, structured, domain-specific

### **Interaction Patterns**

1. **Memory → Knowledge**: Extract facts from conversations into knowledge base
2. **Knowledge → Memory**: Use knowledge to enhance conversation context
3. **Co-evolution**: Memory and knowledge inform each other over time

## Future Extensions

- **Semantic Search**: Vector-based retrieval of relevant conversation segments
- **Multi-modal Memory**: Support for images, documents, and other media
- **Hierarchical Memory**: Short-term, medium-term, and long-term memory layers
- **Memory Compression**: Advanced summarization and compression techniques 