<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

Implementation examples demonstrating DXA framework usage.

## Basic Examples

- **template.py**: Minimal working example showing core patterns
- **chat_bot.py**: Interactive conversational agent
- **research_assistant.py**: Information gathering and analysis
- **system_monitor.py**: Continuous system monitoring

## Advanced Examples

- **collaborative.py**: Multi-agent coordination
- **data_analysis.py**: Data processing and visualization
- **web_automation.py**: Web interaction and scraping

## Usage

Each example can be run directly:

```bash
python examples/chat_bot.py
```

## Common Patterns

1. Agent Creation:
```python
agent = Agent("name")\
    .with_reasoning("type")\
    .with_resources({...})\
    .with_capabilities([...])
```

2. Task Execution:
```python
async with agent:
    result = await agent.run(task)
```

3. Resource Management:
```python
agent.with_resources({
    "llm": LLMResource(model="gpt-4"),
    "custom": CustomResource()
})
```

## Example Structure

Each example demonstrates:
- Appropriate reasoning pattern selection
- Resource configuration
- Task structuring
- Error handling
- Proper cleanup using context managers

See individual examples for detailed implementations.
