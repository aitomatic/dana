<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

## dxa.examples Module

Implementation examples demonstrating DXA framework usage.

## Basic Examples

- **basic/loggable_example.py**: Example of using the Loggable base class
- **execution/workflow/simple_qa.py**: Simple question answering workflow
- **execution/workflow/default_workflow.py**: Default workflow example
- **execution/planning/simple_plan.py**: Basic planning pattern

## Advanced Examples

- **execution/workflow/prosea_workflow.py**: ProSEA framework implementation
- **execution/workflow/complex_research.py**: Multi-step research pattern
- **execution/workflow/system_health.py**: System monitoring example

## Usage

Each example can be run directly:

```bash
python examples/execution/workflow/simple_qa.py
```

## Common Patterns

1. Agent Creation:

```python
from dxa.agent import Agent
from dxa.agent.resource import LLMResource
from dxa.execution import ReasoningStrategy

agent = Agent(name="name")\
    .with_reasoning(ReasoningStrategy.DEFAULT)\
    .with_llm(LLMResource())\
    .with_capabilities({...})
```

2. Task Execution:

```python
# Synchronous execution
result = agent.run(workflow)

# Asynchronous execution
async with agent:
    result = await agent.async_run(workflow)
```

3. Resource Management:

```python
agent.with_llm(LLMResource(config={"model": "openai:gpt-4"}))
agent.with_resources({
    "custom": CustomResource()
})
```

## Example Categories

The example directory is organized by module and functionality:

- **basic/**: Fundamental utilities
  - Logging utilities
  - Loggable class usage
  
- **execution/**: Execution system examples
  - **workflow/**: Workflow definition and execution
  - **planning/**: Planning system usage
  - **reasoning/**: Reasoning patterns
  - **pipeline/**: Data pipeline examples
  
- **resource/**: Resource system examples
  - LLM integration
  - MCP resource examples
  
- **fab-roca/**: Domain-specific examples
  - Semiconductor manufacturing use case
  - RIE monitoring example
  - FDC integration

See individual examples for detailed implementations.
