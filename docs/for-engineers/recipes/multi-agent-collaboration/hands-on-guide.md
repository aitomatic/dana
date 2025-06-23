# Dana Multi-Agent Collaboration - Simple Guide

**Version**: 3.0 - Simplified  
**Date**: January 2025  
**Status**: Production Ready ✅  
**Based on**: `examples/dana/08_a2a_multi_agents/`

## Overview

This simple guide shows Dana's multi-agent collaboration system. You'll learn to use both A2A protocol agents and Dana module agents together.

## Prerequisites

- OpenDXA installed
- Dana language runtime
- Basic Dana syntax knowledge

## Quick Start

### 1. Start A2A Agents

```bash
# Start all agents in background
cd examples/dana/08_a2a_multi_agents/
python start_weather_agent.py --port 5001 &
python start_planner_agent.py --port 5002 &
python start_ticket_agent.py --port 5003 &
sleep 3
```

### 2. Test Basic A2A Usage

```bash
uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/na/use_a2a.na
```

### 3. Test Reason Function with Agents

```bash
uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/na/test_reason_agents.na
```

## Part 1: A2A Agents

### Available Agents

- **Weather Agent (Port 5001)**: Current weather, forecasts
- **Trip Planner Agent (Port 5002)**: Itinerary planning, travel tips  
- **Ticket Agent (Port 5003)**: Event tickets, transport booking

### Basic Usage

```dana
# Create agents
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")
ticket_agent = agent(url="http://localhost:5003")

# Create agent pool
pool = agent_pool(agents=[weather_agent, trip_agent, ticket_agent])

# Use agent directly
result = weather_agent.solve("What is the weather in Tokyo?")

# Use pool selection
selected_agent = pool.select_agent("Plan a trip to Paris")
result = selected_agent.solve("Plan a 3-day trip to Paris")
```

## Part 2: Reason Function with Agents

### Basic Reason Integration

```dana
# Use reason function with specific agents
result = reason("What's the weather in Paris?", agents=[weather_agent])

# Use reason function with agent pool
result = reason("Plan a trip considering weather", agents=pool)

# Use reason function with resource filtering
result = reason("Find weather info", agents=[weather_agent], resources=["websearch"])
```

## Part 3: Module Agents

### Creating Module Agents

**File: `simple_weather.na`**
```dana
# Required system variables
system:agent_name = "Weather Expert"
system:agent_description = "Provides weather analysis"

# Required solve function
def solve(task: str) -> str:
    return reason(f"Analyze weather: {task}")
```

### Using Module Agents

```dana
import simple_weather

# Create module agent
weather_module = agent(module=simple_weather)

# Use like any other agent
result = weather_module.solve("What's the weather in London?")

# Add to agent pool
mixed_pool = agent_pool(agents=[weather_agent, weather_module])
```

## Part 4: Mixed Agent Usage

### Complete Example

```dana
# Import module agents
import weather_expert
import travel_planner

# Create A2A agents
weather_a2a = agent(url="http://localhost:5001")
trip_a2a = agent(url="http://localhost:5002")

# Create module agents
weather_module = agent(module=weather_expert)
travel_module = agent(module=travel_planner)

# Create mixed pool
all_agents = [weather_a2a, trip_a2a, weather_module, travel_module]
pool = agent_pool(agents=all_agents)

# Use mixed pool
task = "Plan a weather-aware trip to Tokyo"
selected = pool.select_agent(task)
result = selected.solve(task)

# Use reason function with mixed agents
reason_result = reason("What's the best time to visit Japan?", agents=all_agents)
```

## Part 5: Simple Workflows

### Sequential Tasks

```dana
# Step-by-step workflow
destination = "Paris"

# Step 1: Get weather
weather_info = weather_agent.solve(f"Weather forecast for {destination}")

# Step 2: Plan trip using weather info
trip_plan = trip_agent.solve(f"Plan trip to {destination} considering: {weather_info}")

# Step 3: Find tickets
tickets = ticket_agent.solve(f"Find tickets for {destination}")

# Step 4: Combine everything
final_plan = reason(f"Create final plan combining: {weather_info}, {trip_plan}, {tickets}")
```

### Multiple Agent Consultation

```dana
# Get different perspectives on same topic (executed sequentially)
topic = "Plan a 5-day trip to Tokyo"

perspectives = {}
perspectives["weather"] = weather_agent.solve(topic)
perspectives["planning"] = trip_agent.solve(topic)
perspectives["tickets"] = ticket_agent.solve(topic)

# Combine all perspectives
final_advice = reason(f"Combine these perspectives: {perspectives}")
```

## Part 6: Agent Discovery

### Basic Agent Information

```dana
# Create agent pool
pool = agent_pool(agents=[weather_agent, trip_agent, ticket_agent])

# Get agent cards
agent_cards = pool.get_agent_cards()

# Display agent information
for agent_name, card in agent_cards.items():
    print(f"Agent: {agent_name}")
    print(f"Description: {card.get('description', 'No description')}")
    print(f"Skills: {card.get('skills', [])}")
```

## Part 7: Resource Filtering

### Controlling Agent Resources

```dana
# Set up resources
websearch = use("mcp", url="http://localhost:8880/websearch")

# Use agents with specific resources only
result = reason("Find current weather online", 
               agents=[weather_agent], 
               resources=["websearch"])

# Use agents with no resources (forces external agent use)
result = reason("What's the weather?", 
               agents=[weather_agent], 
               resources=[])
```

## Part 8: Complete Example

### Simple Travel Planning System

```dana
import weather_expert
import travel_planner

# Create all agents
weather_a2a = agent(url="http://localhost:5001")
trip_a2a = agent(url="http://localhost:5002")
weather_module = agent(module=weather_expert)
travel_module = agent(module=travel_planner)

# Plan a trip
def plan_trip(destination: str, duration: str):
    # Get weather info
    weather = reason(f"Weather for {destination}", agents=[weather_a2a, weather_module])
    
    # Plan itinerary
    itinerary = reason(f"Plan {duration} trip to {destination}", agents=[trip_a2a, travel_module])
    
    # Combine everything
    all_agents = [weather_a2a, trip_a2a, weather_module, travel_module]
    final_plan = reason(f"Create complete plan for {destination}: Weather: {weather}, Itinerary: {itinerary}", agents=all_agents)
    
    return final_plan

# Execute trip planning
result = plan_trip("Tokyo", "5 days")
print(result)
```

## Summary

### Key Features

1. **A2A Agents**: External services (Weather, Trip Planner, Ticket)
2. **Module Agents**: Dana modules with `solve()` function
3. **Agent Pools**: Mixed collections of different agent types
4. **Reason Integration**: Use `reason()` function with `agents=` parameter
5. **Resource Filtering**: Control which resources agents can use

### Basic Patterns

```dana
# Create agents
agent = agent(url="http://localhost:5001")           # A2A agent
module_agent = agent(module=imported_module)         # Module agent

# Use agents
result = agent.solve("task")                         # Direct usage
result = reason("task", agents=[agent])              # Reason function
result = reason("task", agents=pool)                 # Agent pool

# Resource control
result = reason("task", agents=[agent], resources=["websearch"])
```

This simplified guide covers all essential multi-agent functionality without unnecessary complexity. Start with these patterns and add complexity only when needed! 🚀
