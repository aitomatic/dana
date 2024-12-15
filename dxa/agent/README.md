# DXA Agents

This directory contains the core agent implementation for the DXA framework.

## Architecture

The DXA agent system uses a unified, composable design that supports progressive complexity.

### Core Components

#### Agent

The unified Agent class provides a flexible implementation supporting:

- Different reasoning strategies (CoT, OODA)
- Resource management
- I/O handling
- Capability tracking

```python
# Basic usage
agent = Agent("researcher")
result = await agent.run("Analyze this data")

# Progressive configuration
agent = Agent("analyst")\
    .with_reasoning(reasoning)\
    .with_resources(resources)\
    .with_capabilities(["analysis", "research"])\
    .with_io(io_handler)
```

#### Runtime

AgentRuntime manages execution:

- State management
- Iteration control
- Progress tracking
- Error handling

#### Factory

Factory provides lifecycle management:

```python
async with create_agent({
    "name": "researcher",
    "reasoning": "cot",
    "capabilities": ["research"],
    "resources": {
        "llm": LLMResource(model="gpt-4")
    }
}) as agent:
    result = await agent.run("Research quantum computing")
```

### Key Features

1. **Progressive Complexity**
   - Start simple with sensible defaults
   - Add capabilities as needed
   - Configure for specific use cases

2. **Resource Management**
   - LLM integration
   - Expert knowledge
   - Tool access
   - I/O handling

3. **Reasoning Integration**
   - Chain of Thought (CoT)
   - OODA Loop
   - Custom reasoning patterns

4. **State Management**
   - Execution tracking
   - Progress monitoring
   - History recording

## Components

### Core Classes

- `Agent`: Unified agent implementation
- `AgentRuntime`: Execution management
- `StateManager`: State tracking
- `AgentConfig`: Configuration management

### Supporting Types

- `AgentProgress`: Progress tracking
- `Observation`: Agent observations
- `Message`: Communication records

## Usage Examples

### Basic Agent

```python
agent = Agent()
result = await agent.run("Analyze this data")
```

### Research Agent

```python
agent = Agent("researcher")\
    .with_reasoning("cot")\
    .with_resources({
        "llm": LLMResource(model="gpt-4"),
        "search": SearchResource()
    })
result = await agent.run("Research quantum computing")
```

### Interactive Agent

```python
agent = Agent("assistant")\
    .with_reasoning("ooda")\
    .with_io(WebSocketIO())
result = await agent.run("Help user with task")
```
