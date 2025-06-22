# Multi-Agent Collaboration with Dana

This directory contains **simple, straightforward examples** of Dana's multi-agent collaboration system. The examples demonstrate both A2A (Agent-to-Agent) protocol agents and Dana module agents working together.

## Quick Start

1. **Start the existing A2A agents** (from `examples/dana/08_a2a_multi_agents/`):
   ```bash
   # Terminal 1 - Weather Agent
   cd examples/dana/08_a2a_multi_agents/
   python start_weather_agent.py --port 5001
   
   # Terminal 2 - Trip Planner Agent  
   cd examples/dana/08_a2a_multi_agents/
   python start_planner_agent.py --port 5002
   
   # Terminal 3 - Ticket Agent
   cd examples/dana/08_a2a_multi_agents/
   python start_ticket_agent.py --port 5003
   ```

2. **Run the complete demo** (now located in examples):
   ```bash
   uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/module_agents/demo_main.na
   ```

## Example Files Location

The module agent examples have been moved to:
**`examples/dana/08_a2a_multi_agents/module_agents/`**

This includes:
- `weather_expert.na` - Simple weather analysis module agent
- `travel_planner.na` - Simple travel planning module agent  
- `demo_main.na` - Complete demo showing both A2A and module agents
- `README.md` - Quick start guide for the examples

## What You'll Learn

### Core Multi-Agent Features
- **Agent Creation**: Both A2A and module agents
- **Agent Pools**: Managing multiple agents together  
- **Agent Selection**: Automatic selection based on task
- **Reason Integration**: Using agents with the reason function
- **Resource Filtering**: Controlling which resources agents can use

### Simple Examples Included

#### `demo_main.na` - Complete Demo
Simple demonstration showing:
- Creating A2A agents
- Creating module agents from Dana files
- Creating mixed agent pools
- Basic agent usage (both types)
- Agent pool selection
- Reason function with agents
- Resource filtering

#### `weather_expert.na` - Module Agent
Basic weather analysis agent with:
- Required system variables
- Simple solve function
- Web search integration
- Helper functions for weather analysis

#### `travel_planner.na` - Module Agent  
Basic travel planning agent with:
- Trip planning functionality
- Accommodation finding
- Cost estimation
- Web search integration

## Architecture Overview

Dana's multi-agent system supports two types of agents:

### A2A (Agent-to-Agent) Protocol Agents
- External agents running as separate services
- Connected via HTTP/WebSocket
- Examples: Weather, Trip Planner, Ticket agents

### Dana Module Agents
- Native Dana modules with agent capabilities
- Defined in `.na` files with required functions
- Integrated directly into Dana runtime

### Unified Agent Interface
Both agent types work seamlessly together:
- Same `solve()` method interface
- Compatible with agent pools
- Work with reason function
- Support resource filtering

## Key Concepts

### Agent Pools
```dana
pool = agent_pool(agents=[agent1, agent2, agent3])
selected = pool.select_agent("task description")
```

### Reason Function Integration
```dana
# With specific agents
result = reason("task", agents=[weather_agent])

# With agent pool  
result = reason("task", agents=pool)

# With resource filtering
result = reason("task", agents=[agent], resources=["websearch"])
```

### Module Agent Requirements
```dana
# Required system variables
system:agent_name = "Agent Name"
system:agent_description = "What the agent does"

# Required solve function
def solve(task: str) -> str:
    return process_task(task)
```

## Requirements

- **A2A Agents**: Start the existing agents from `examples/dana/08_a2a_multi_agents/`
- **MCP Resources**: Web search server at `http://localhost:8880/websearch`
- **Dana Runtime**: OpenDXA with Dana language support

## Building on Existing Examples

These examples build upon the foundation in `examples/dana/08_a2a_multi_agents/`:
- `use_a2a.na` - Basic A2A agent usage patterns
- `test_reason_agents.na` - Advanced reason function with agents
- `test_reason_with_resources.na` - Resource filtering examples
- `agent_1.na` - Simple module agent pattern

The module agent examples in `module_agents/` show how to combine these patterns into complete multi-agent workflows.

## Next Steps

1. **Start with the demo**: Run the demo in `examples/dana/08_a2a_multi_agents/module_agents/demo_main.na`
2. **Create your own module agents**: Follow the pattern in the example files
3. **Build agent workflows**: Combine multiple agents for complex tasks
4. **Explore advanced features**: Check the hands-on guide for detailed examples

Dana's multi-agent system provides a simple yet powerful foundation for building sophisticated AI agent collaborations! 