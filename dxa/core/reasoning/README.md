<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Reasoning Patterns

This module provides different reasoning strategies with increasing complexity.

## Available Patterns

### 1. DirectReasoning

- Simple direct execution without complex reasoning
- Best for straightforward tasks with clear steps
- Lowest overhead, fastest execution
- Use when: Task is well-defined and needs quick execution

### 2. ChainOfThoughtReasoning

- Linear step-by-step reasoning with explicit thought process
- Best for problems requiring detailed explanation
- Includes understanding, analysis, solution, and verification
- Use when: Need transparency in reasoning process

### 3. OODAReasoning

- Observe-Orient-Decide-Act loop for dynamic situations
- Best for problems requiring continuous adaptation
- Handles changing conditions and requirements
- Use when: Environment is dynamic and needs constant reassessment

### 4. DANAReasoning

- Domain-Aware Neurosymbolic Agent combining neural and symbolic approaches
- Best for problems requiring precise computation with domain knowledge
- Bridges LLM reasoning with symbolic execution
- Use when: Need precise domain-specific computation

## Usage

### 1. Through Agent (Recommended)

```python
agent = Agent("researcher", llm=my_llm)\
    .with_reasoning("direct")  # or "cot", "ooda", "dana"
result = await agent.run("Research quantum computing")
```

### 2. Direct Usage (Advanced)

```python
# Create reasoning instance
reasoning = DirectReasoning(config=ReasoningConfig(
    agent_llm=my_llm,
    temperature=0.7
))

# Create context
context = ReasoningContext(
    objective="Research quantum computing",
    resources={"search": search_resource},
    workspace={},
    history=[]
)

# Execute reasoning
result = await reasoning.reason_about(
    task={"command": "Find recent papers"},
    context=context
)
```

## Core Components

- **ReasoningContext**: Maintains state and resources
- **ReasoningConfig**: Configuration for reasoning behavior
- **ReasoningResult**: Structured output from reasoning
- **ObjectiveState**: Tracks objective refinements

## Best Practices

1. Start with DirectReasoning for simple tasks
2. Use ChainOfThought when explanation is important
3. Choose OODA for dynamic environments
4. Use DANA for domain-specific computation
5. Monitor and adjust based on task complexity
