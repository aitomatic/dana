<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Capabilities

Capabilities define the core competencies and abilities of DXA agents.

## Built-in Capabilities

- **Memory**: Experience and knowledge retention
- **Planning**: Task decomposition and sequencing
- **Learning**: Adaptation and improvement
- **Expertise**: Domain-specific knowledge

## Interface

Capabilities implement BaseCapability:

```python
class CustomCapability(BaseCapability):
    async def initialize(self) -> None:
        """Set up capability"""
        pass

    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use capability in context"""
        pass
```

## Usage

```python
agent = Agent("researcher")\
    .with_capabilities([
        "memory",
        "planning",
        CustomCapability()
    ])
```

See tests for implementation examples. 