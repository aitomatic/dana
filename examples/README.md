<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

This directory contains example implementations and use cases for the DXA (Domain-Expert Agent) framework. These examples demonstrate various capabilities and features of the framework, seen from the perspective of a DXA library developer (e.g., an AI Solution Engineer).

For a complete overview of DXA, see the [architecture documentation](../dxa/README.md) or the [overall project README](../README.md).

## Available Examples

### Interactive Math (`interactive_math.py`)
An interactive math tutor agent that helps solve mathematical problems step by step. This example demonstrates:
- Basic agent setup with GPT-4
- Interactive console-based communication
- Chain of Thought reasoning
- Structured system prompts
- Environment variables: `OPENAI_API_KEY`

### Web Scraping Automation (`automation_web.py`)
An automation agent designed for web scraping tasks with a defined workflow. This example demonstrates:
- Automation agent implementation
- Step-by-step workflow execution
- Result validation
- Resource cleanup
- Environment variables: `OPENAI_API_KEY`

### WebSocket Solver (`websocket_solver.py`)
A WebSocket-based problem-solving agent that provides progress updates. This example demonstrates:
- WebSocket communication
- Progress tracking
- OODA Loop reasoning principles
- Asynchronous execution
- Environment variables: `OPENAI_API_KEY`, `WEBSOCKET_URL`

### Collaborative Research (`collaborative_research.py`)
A multi-agent system coordinating research tasks between specialized agents. This example demonstrates:
- Multi-agent coordination
- Mixed communication methods (Console and WebSocket)
- Different reasoning strategies
- State history tracking
- Environment variables: `OPENAI_API_KEY`, `WEBSOCKET_URL`

## Running the Examples

1. Make sure you have DXA installed and properly configured with your Aitomatic credentials
2. Set up the required environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
export WEBSOCKET_URL="your-websocket-url"  # Required for WebSocket examples
```
3. Navigate to the examples directory:
```bash
cd examples
```
4. Run any example using Python:
```bash
python interactive_math.py  # or any other example file
```

## Creating Your Own Examples

When creating new examples:
1. Create a new Python file in this directory
2. Include clear documentation and comments
3. Demonstrate specific features or capabilities of DXA
4. Follow the existing example structure for consistency

### Basic DXA Architecture (Using interactive_math.py)

The interactive math example demonstrates the fundamental architecture of a DXA agent:

1. **Agent Configuration**:
```python
agent_config = {
    "name": "math_tutor",
    "model": "gpt-4",
    "temperature": 0.7,
    "api_key": api_key,
    "system_prompt": "...",
    "reasoning": {
        "strategy": "cot"
    }
}
```

2. **Agent Components**:
- **Base Agent**: InteractiveAgent class that handles core agent functionality
- **Reasoning**: ChainOfThoughtReasoning for structured problem-solving
- **I/O**: Console-based interaction for user communication
- **Capabilities**: Built-in mathematical expertise

3. **Execution Flow**:
```python
# Create agent instance
agent = InteractiveAgent(
    config=agent_config,
    reasoning=ChainOfThoughtReasoning()
)

# Run agent asynchronously
result = await agent.run()
```

4. **Error Handling**:
- Environment variable validation
- Configuration error checking
- Runtime error management

This architecture provides a template for creating new agents with different capabilities and interaction modes.

## Support

If you have questions about the examples or need assistance:
- Refer to the official DXA documentation
- Contact Aitomatic support
- Reach out to your Aitomatic representative

## License

These examples are proprietary and confidential to Aitomatic, Inc. All rights reserved.