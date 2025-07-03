# Dana Language Interface: OpenDXA KNOWS Knowledge Retrieval

## Simple User Interface

### 1. Knowledge Base Loading
```dana
# One line to load knowledge pack (contains both vector DB and structured data)
private:kb = load_knowledge_pack("path/to/knowledge_pack")
```

### 2. Context Management
```dana
# Create a context manager
private:ctx = create_context_manager()

# Update context (automatically tracks history)
private:ctx.update({
    "user_level": "expert",
    "system_state": "running"
})

# Context is automatically maintained between queries
```

### 3. Simple Knowledge Retrieval
```dana
# Basic query with context
result = query_knowledge("How to reset the system?", context=private:ctx)

# That's it! The system automatically:
# - Determines if it's a workflow or semantic query
# - Uses appropriate retrieval method
# - Maintains context
# - Returns best matching results
```

### 4. Common Usage Patterns

#### Pattern 1: Simple Knowledge Retrieval
```dana
# Load knowledge and create context
private:kb = load_knowledge_pack("path/to/knowledge_pack")
private:ctx = create_context_manager()

# Query knowledge
result = query_knowledge("How to reset the system?", context=private:ctx)
```

#### Pattern 2: Contextual Knowledge Retrieval
```dana
# Update context before querying
private:ctx.update({
    "user_level": "expert",
    "system_state": "running"
})
result = query_knowledge("How to reset the system?", context=private:ctx)
```

#### Pattern 3: Error Handling
```dana
try:
    result = query_knowledge("How to reset the system?", context=private:ctx)
except KnowledgeNotFound:
    log("Knowledge not found, using fallback", "warn")
    result = get_fallback_response()
```

## Under the Hood

The system automatically handles:

1. **Knowledge Organization**
   - Detects query type (workflow vs semantic)
   - Uses appropriate retrieval method
   - Combines results if needed

2. **Context Management**
   - Maintains query history
   - Tracks user preferences
   - Records system state
   - Manages session context

3. **Result Processing**
   - Ranks results by relevance
   - Filters by context
   - Formats output appropriately
   - Handles errors gracefully

## Example Usage Scenarios

### Scenario 1: Basic Knowledge Retrieval
```dana
# Load knowledge pack
private:kb = load_knowledge_pack("path/to/knowledge_pack")
private:ctx = create_context_manager()

# Simple query
result = query_knowledge("How to reset the system?", context=private:ctx)
```

### Scenario 2: Contextual Knowledge Retrieval
```dana
# Update context with user level
private:ctx.update({"user_level": "beginner"})

# Query with context
result = query_knowledge("How to reset the system?", context=private:ctx)
```

### Scenario 3: Error Handling
```dana
try:
    result = query_knowledge("How to reset the system?", context=private:ctx)
except KnowledgeNotFound:
    log("Knowledge not found", "warn")
    result = get_fallback_response()
```

## Best Practices

1. **Knowledge Pack Organization**
   - Keep knowledge packs organized by domain
   - Use descriptive names for knowledge packs
   - Maintain consistent structure

2. **Context Management**
   - Update context when user state changes
   - Clear context when switching domains
   - Use appropriate context levels

3. **Error Handling**
   - Always use try-catch for queries
   - Provide fallback responses
   - Log errors appropriately

## Implementation Notes

### Knowledge Pack Structure
```
knowledge_pack/
├── vector_db/           # LlamaIndex vector database
│   └── ...
├── workflows/          # Structured workflow data
│   └── ...
└── metadata.json      # Pack metadata and configuration
```

### Context Manager
```dana
struct ContextManager:
    history: list
    user_state: dict
    system_state: dict
    preferences: dict
```

### Query Result
```dana
struct QueryResult:
    content: str
    type: str  # "workflow" or "semantic"
    score: float
    source: str
    metadata: dict
``` 