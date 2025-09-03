# Module Agents Examples

This directory contains Dana module agent examples that work alongside the A2A agents in the parent directory.

## Files

- **`weather_expert.na`** - Simple weather analysis module agent
- **`travel_planner.na`** - Simple travel planning module agent  
- **`demo_main.na`** - Complete demo showing both A2A and module agents working together

## Quick Start

1. **Start the A2A agents** (run in background):
   ```bash
   # From the parent directory - all in one terminal
   cd examples/dana/08_a2a_multi_agents/
   python start_weather_agent.py --port 5001 &
   python start_planner_agent.py --port 5002 &
   python start_ticket_agent.py --port 5003 &
   
   # Wait for agents to start
   sleep 3
   ```

2. **Run the complete demo** (from this directory):
   ```bash
   # Method 1: Navigate to this directory (simple)
   # After starting A2A agents, we are in examples/dana/08_a2a_multi_agents/
   cd module_agents
   uv run python -m dana.dana.exec.dana demo_main.na
   
   # Method 2: Use DANA_PATH from anywhere
   export DANA_PATH=/path/to/opendxa/examples/dana/08_a2a_multi_agents/module_agents
   uv run python -m dana.dana.exec.dana examples/dana/08_a2a_multi_agents/module_agents/demo_main.na
   ```

## Important Notes

### Import Requirements
- **Dana module imports only work when running from the directory containing the `.na` files**
- The `import weather_expert` and `import travel_planner` statements in `demo_main.na` require running from this directory

### Alternative: Using DANA_PATH
You can set the `DANA_PATH` environment variable to enable imports from any directory:

```bash
# From OpenDXA root directory
export DANA_PATH=$(pwd)/examples/dana/08_a2a_multi_agents/module_agents
uv run python -m dana.dana.exec.dana examples/dana/08_a2a_multi_agents/module_agents/demo_main.na

# Or inline
DANA_PATH=$(pwd)/examples/dana/08_a2a_multi_agents/module_agents uv run python -m dana.dana.exec.dana examples/dana/08_a2a_multi_agents/module_agents/demo_main.na
```

### MCP Resource Adaptation
- The examples use `websearch.openai_websearch()` but **your MCP server may have different methods**
- Check your MCP server documentation and adapt the resource calls accordingly:
  ```dana
  # Adapt to your MCP server's actual methods
  # result = websearch.query(search_term)
  # result = websearch.web_search(query)  
  # result = websearch.search_web(text)
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

## Troubleshooting

### Import Errors
- **Problem**: `ImportError: No module named 'weather_expert'`
- **Solution 1**: Make sure you're running from this `module_agents/` directory
- **Solution 2**: Set `DANA_PATH` environment variable: `export DANA_PATH=$(pwd)/examples/dana/08_a2a_multi_agents/module_agents`

### MCP Resource Errors  
- **Problem**: `AttributeError: 'MCPResource' object has no attribute 'search'`
- **Solution**: Update the resource method calls to match your MCP server's API

### A2A Connection Errors
- **Problem**: A2A agents not responding
- **Solution**: Check agents are running with `ps aux | grep python` and restart if needed

This demonstrates Dana's unified multi-agent architecture!

## Agent Pool Management

Managing multiple agents efficiently requires careful consideration of:

- **Pool Initialization**: Setting up agent pools with proper resource allocation
- **Load Balancing**: Distributing tasks across available agents
- **Health Monitoring**: Checking agent status and handling failures
- **Dynamic Scaling**: Adding or removing agents based on demand

Example agent pool configuration:

```dana
struct AgentPool:
    agents: list
    max_concurrent_tasks: int
    health_check_interval: int
    
def create_agent_pool(config: dict) -> AgentPool:
    pool = AgentPool(
        agents=[],
        max_concurrent_tasks=config.get("max_concurrent", 10),
        health_check_interval=config.get("health_interval", 30)
    )
    
    # Initialize agents based on configuration
    for agent_config in config.get("agents", []):
        agent = create_agent(agent_config)
        pool.agents.append(agent)
    
    return pool
```

## Reason Function Integration

The `reason()` function provides seamless integration with multi-agent systems:

- **Agent Selection**: Automatically choose the best agent for a task
- **Context Sharing**: Share context between agents efficiently
- **Result Aggregation**: Combine results from multiple agents
- **Error Handling**: Graceful fallback when agents fail

Example reason function usage with agents:

```dana
def solve_complex_task(task: str, agents: list) -> str:
    # Use reason function to coordinate agents
    result = reason(
        f"Solve this task using the available agents: {task}",
        context=[task, agents],
        agents=agents,
        strategy="best_match"
    )
    
    return result
``` 