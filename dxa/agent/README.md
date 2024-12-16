<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Agent System

The agent system provides the core agent implementation and runtime environment.

## Components

- **Agent**: Main agent class with fluent configuration
- **AgentRuntime**: Execution environment and state management
- **AgentLLM**: Language model integration
- **AgentProgress**: Task progress tracking

## Agent Configuration

```python
# Basic setup
agent = Agent("researcher")\
    .with_reasoning("cot")\
    .with_resources({"llm": my_llm})

# Advanced configuration
agent = Agent("analyst", 
    config=AgentConfig(
        reasoning_level="ooda",
        max_iterations=10,
        temperature=0.7
    ))
```

## Execution Flow

1. Agent receives task
2. Runtime prepares execution context
3. Reasoning system processes task
4. Resources are accessed as needed
5. Results are returned through I/O

See tests for detailed usage examples.
