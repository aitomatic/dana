# Resource Examples

This directory contains examples demonstrating resource management and integration in the DXA framework. Resources are components that provide capabilities to agents, such as language models, databases, and external services.

## Learning Paths

### Core Concepts [Intermediate]

These examples demonstrate key resource concepts:

- [llm_resource.py](llm_resource.py): LLM integration
  - Configuring LLM resources
  - Using LLMs in agents
  - Managing LLM interactions

### Advanced Patterns [Advanced]

These examples demonstrate advanced resource patterns:

- [mcp/mcp_agent_demo.py](mcp/mcp_agent_demo.py): MCP integration
  - Using the Model Control Plane
  - Advanced resource configuration
  - Managing model deployments

- [mcp/mcp_echo_service.py](mcp/mcp_echo_service.py): MCP service implementation
  - Creating custom MCP services
  - Service configuration
  - Request/response handling

## Key Concepts

### Resource Creation

```python
from dxa.agent.resource import LLMResource

# Create an LLM resource
llm = LLMResource(
    config={
        "model": "openai:gpt-4",
        "temperature": 0.7
    }
)
```

### Resource Integration

```python
from dxa.agent import Agent

# Add resources to an agent
agent = Agent(name="example_agent")
agent.with_llm(LLMResource())
agent.with_resources({
    "custom": CustomResource()
})
```

### Resource Usage

```python
# Using a resource
async with agent:
    response = await agent.resources.llm.query({
        "prompt": "Explain quantum computing",
        "max_tokens": 100
    })
    
    result = response.get("content")
```

## Related Concepts

- [Workflow Examples](../execution/workflow/): How resources are used in workflows
- [Reasoning Examples](../execution/reasoning/): How resources support reasoning

## Next Steps

After exploring these examples, consider:

1. Creating custom resources
2. Implementing resource caching
3. Exploring resource composition
4. Developing domain-specific resources 