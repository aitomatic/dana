<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

Implementation examples and usage patterns for the DXA framework.

## Basic Examples

- **chat_bot.py**: Simple conversational agent
- **system_monitor.py**: System monitoring and reporting
- **research_assistant.py**: Information gathering and analysis
- **template.py**: Starter template for new agents

## Usage

Each example can be run directly:

```bash
python examples/chat_bot.py
```

Or imported as a reference:

```python
from examples.template import create_basic_agent

agent = create_basic_agent()
await agent.run("Hello!")
```

## Example Structure

Each example follows:

1. Configuration setup
2. Resource initialization
3. Agent creation and setup
4. Task execution
5. Cleanup and shutdown

See individual example files for detailed documentation.
