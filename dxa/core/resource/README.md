<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Resource System

Resources provide agents with access to external tools, services, and capabilities.

## Core Resources

- **LLMResource**: Language model integration
- **HumanResource**: Human-in-the-loop interaction
- **AgentResource**: Inter-agent communication
- **ExpertResource**: Domain expert consultation

## Resource Interface

All resources implement BaseResource:

```python
class CustomResource(BaseResource):
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource request"""
        pass

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled"""
        pass
```

## Resource Management

Resources are managed through the agent interface:

```python
agent = Agent("researcher")\
    .with_resources({
        "llm": LLMResource(model="gpt-4"),
        "human": HumanResource(),
        "expert": ExpertResource("domain")
    })
```

See individual resource implementations for detailed usage. 