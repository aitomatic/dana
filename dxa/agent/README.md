<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Agent System

The DXA agent system implements a composable architecture that combines planning, reasoning, and execution to create powerful AI agents.

## Design Philosophy

1. Simple things should be simple, complex things should be possible
2. Composition over inheritance
3. Smart defaults with explicit control when needed

## Core Components

```mermaid
graph TB
    A[Agent] --> B[Planning]
    A --> C[Reasoning]
    A --> D[Resources]
    A --> E[Capabilities]
    A --> F[IO]
```

## Usage

```python
# Simple usage with defaults
agent = Agent("assistant")
result = await agent.run("Help me with this task")

# Full control with composition
agent = Agent("expert")\
    .with_planning("hierarchical")\
    .with_reasoning("cot")\
    .with_resources({"llm": my_llm})\
    .with_capabilities(["research"])\
    .with_io(custom_io)

# Execution with context
async with agent:
    result = await agent.run(task)
```

## Agent Construction

+ ### LLM Requirement
+ 
+ Every DXA agent requires an LLM that powers its cognitive functions:
+ ```python
+ # The LLM is provided at construction
+ agent = Agent("assistant", llm=LLMResource("gpt-4"))
+ 
+ # It's automatically used by planning and reasoning
+ agent.with_planning("hierarchical")  # Uses agent's LLM
+ agent.with_reasoning("cot")          # Uses agent's LLM
+ ```
+ 
[Rest of agent-specific documentation...]
