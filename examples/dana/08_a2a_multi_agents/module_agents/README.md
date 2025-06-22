# Module Agents Examples

This directory contains Dana module agent examples that work alongside the A2A agents in the parent directory.

## Files

- **`weather_expert.na`** - Simple weather analysis module agent
- **`travel_planner.na`** - Simple travel planning module agent  
- **`demo_main.na`** - Complete demo showing both A2A and module agents working together

## Quick Start

1. **Start the A2A agents** (from parent directory):
   ```bash
   cd examples/dana/08_a2a_multi_agents/
   python start_weather_agent.py --port 5001
   python start_planner_agent.py --port 5002
   python start_ticket_agent.py --port 5003
   ```

2. **Run the complete demo**:
   ```bash
   uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/module_agents/demo_main.na
   ```

## Module Agent Pattern

Each module agent follows this simple pattern:

```dana
# Required system variables
system:agent_name = "Agent Name"
system:agent_description = "What the agent does"

# Required solve function
def solve(task: str) -> str:
    return process_task(task)
```

## Integration with A2A Agents

The demo shows how module agents and A2A agents work seamlessly together:
- Mixed agent pools containing both types
- Same `solve()` interface for both
- Compatible with reason function
- Support for resource filtering

This demonstrates Dana's unified multi-agent architecture! 