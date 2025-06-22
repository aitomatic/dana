# Dana Multi-Agent Collaboration - Hands-On Guide

**Version**: 2.0  
**Date**: January 2025  
**Status**: Production Ready ✅  
**Based on**: `examples/dana/08_a2a_multi_agents/`

## Overview

This hands-on guide demonstrates Dana's complete multi-agent collaboration system, building upon the existing examples in `examples/dana/08_a2a_multi_agents/`. You'll learn to orchestrate both A2A protocol agents and Dana module agents for complex workflows.

## Prerequisites

- OpenDXA installed and configured
- Dana language runtime available
- Basic understanding of Dana syntax
- Optional: Running A2A agents (Weather, Trip Planner, Ticket agents)

## Quick Start

### 1. Run Existing A2A Agents

First, start the pre-built A2A agents from the examples:

```bash
# Terminal 1 - Weather Agent
uv run python examples/dana/08_a2a_multi_agents/start_weather_agent.py --port 5001

# Terminal 2 - Trip Planner Agent  
uv run python examples/dana/08_a2a_multi_agents/start_planner_agent.py --port 5002

# Terminal 3 - Ticket Agent
uv run python examples/dana/08_a2a_multi_agents/start_ticket_agent.py --port 5003
```

### 2. Test Basic A2A Integration

```bash
# Run the basic A2A example
uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/na/use_a2a.na
```

### 3. Test Advanced Reason Function

```bash
# Run the reason function with agents
uv run python -m opendxa.dana.exec.dana examples/dana/08_a2a_multi_agents/na/test_reason_agents.na
```

## Part 1: Understanding Existing A2A Agents

### Available A2A Agents

The existing examples provide three specialized agents:

#### 1. Weather Agent (Port 5001)
- **Skills**: Current weather, multi-day forecasts
- **Locations**: Paris, Tokyo, New York, London, San Francisco, Sydney, Berlin
- **Usage**: Weather queries, travel weather advice

#### 2. Trip Planner Agent (Port 5002)  
- **Skills**: Itinerary planning, travel tips
- **Features**: Multi-day itineraries, location-specific advice
- **Usage**: Trip planning, travel recommendations

#### 3. Ticket Agent (Port 5003)
- **Skills**: Event tickets, transport booking
- **Features**: Event search, transport reservations
- **Usage**: Ticket booking, event discovery

### Basic A2A Usage Pattern

From `examples/dana/08_a2a_multi_agents/na/use_a2a.na`:

```dana
# Create individual agents
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")
ticket_agent = agent(url="http://localhost:5003")

# Create agent pool
pool = agent_pool(agents=[weather_agent, trip_agent, ticket_agent])

# Select and use agent
task = "What is the weather in Tokyo?"
selected_agent = pool.select_agent(task)

if selected_agent != None:
    print(selected_agent.solve(task))
else:
    print(reason(task, enable_ipv=False))
```

## Part 2: Advanced Reason Function Integration

### New Agents Parameter

The `reason` function now supports direct agent integration:

```dana
# From examples/dana/08_a2a_multi_agents/na/test_reason_agents.na

# Agent list approach
task = "What's the weather like in Paris for travel planning?"
result = reason(task, agents=[weather_agent, trip_agent], enable_ipv=False)

# Agent pool approach  
pool = agent_pool(agents=[weather_agent, trip_agent, ticket_agent])
task = "Plan a complete trip to Tokyo including weather and flights"
result = reason(task, agents=pool, enable_ipv=False)
```

### Resource Filtering with Agents

From `examples/dana/08_a2a_multi_agents/na/test_reason_with_resources.na`:

```dana
# Set up resources
websearch = use("mcp", url="http://localhost:8880/websearch")
weather_service = use("mcp", url="http://localhost:8881/weather")

# Agent selection with limited resources
task = "What's the weather like in Paris?"
result = reason(task, agents=[weather_agent, trip_agent], resources=["websearch"])

# Agent selection with no resources (forces external agent use)
task = "What's the weather in London?"
result = reason(task, agents=[weather_agent, trip_agent], resources=[])
```

## Part 3: Module Agents Deep Dive

### Creating Module Agents

From `examples/dana/08_a2a_multi_agents/na/agent_1.na`:

```dana
# Module agent requirements
system:agent_name = "Weather Agent"
system:agent_description = "Weather Agent is a helpful assistant that can answer questions and help with tasks."

# Resources available to this agent
websearch = use("mcp", url="http://localhost:8880/websearch")

# Required solve function
def solve(task: str) -> str:
    return reason(task)
```

### Using Module Agents

From `examples/dana/08_a2a_multi_agents/na/module_agent_functionality.na`:

```dana
import agent_1

# Direct module usage
print(agent_1.solve("What is the weather in Tokyo?"))

# Module as agent
module_agent_1 = agent(module=agent_1)

# Inspect agent properties
print(module_agent_1.agent_card)

# Use as agent
print(module_agent_1.solve("What is the weather in Tokyo?"))
```

## Part 4: Building Advanced Module Agents

Let's create more sophisticated module agents building on the existing patterns:

### Advanced Weather Expert Module

**File: `advanced_weather_expert.na`**
```dana
# Enhanced weather expert with multiple capabilities
system:agent_name = "Advanced Weather Expert"
system:agent_description = "Comprehensive weather analysis agent with forecasting and travel advice"

# Multiple resources for enhanced capabilities
websearch = use("mcp", url="http://localhost:8880/websearch")

def solve(task: str) -> str:
    log(f"Advanced Weather Expert processing: {task}")
    
    # Enhanced reasoning with context
    if "forecast" in task.lower():
        return reason(f"Provide detailed weather forecast analysis: {task}")
    elif "travel" in task.lower():
        return reason(f"Provide weather-based travel recommendations: {task}")
    else:
        return reason(f"Provide comprehensive weather analysis: {task}")

# Additional specialized functions
def get_travel_weather_advice(destination: str, dates: str) -> str:
    """Get weather advice for travel planning"""
    return reason(f"Analyze weather conditions for traveling to {destination} during {dates}")

def compare_weather_locations(locations: list) -> str:
    """Compare weather across multiple locations"""
    location_str = ", ".join(locations)
    return reason(f"Compare and analyze weather conditions across: {location_str}")

def seasonal_weather_analysis(location: str, season: str) -> str:
    """Analyze seasonal weather patterns"""
    return reason(f"Analyze {season} weather patterns and trends for {location}")
```

### Multi-Modal Travel Assistant

**File: `travel_assistant.na`**
```dana
system:agent_name = "Travel Assistant"
system:agent_description = "Comprehensive travel planning agent with weather integration and booking capabilities"

websearch = use("mcp", url="http://localhost:8880/websearch")

def solve(task: str) -> str:
    log(f"Travel Assistant processing: {task}")
    
    # Task routing based on content
    task_lower = task.lower()
    
    if "weather" in task_lower:
        return reason(f"Provide weather-aware travel planning: {task}")
    elif "itinerary" in task_lower or "plan" in task_lower:
        return reason(f"Create detailed travel itinerary: {task}")
    elif "budget" in task_lower or "cost" in task_lower:
        return reason(f"Analyze travel costs and budget planning: {task}")
    else:
        return reason(f"Provide comprehensive travel assistance: {task}")

def create_weather_aware_itinerary(destination: str, days: int, season: str) -> str:
    """Create itinerary considering weather conditions"""
    return reason(f"Create {days}-day weather-aware itinerary for {destination} in {season}")

def estimate_travel_budget(destination: str, duration: str, style: str) -> str:
    """Estimate travel budget with different styles"""
    return reason(f"Estimate {style} travel budget for {duration} trip to {destination}")

def find_seasonal_activities(destination: str, season: str) -> str:
    """Find activities suitable for specific seasons"""
    return reason(f"Find {season} activities and attractions in {destination}")
```

## Part 5: Comprehensive Multi-Agent Workflows

### Sequential Agent Collaboration

**File: `sequential_collaboration.na`**
```dana
# Import our enhanced modules
import advanced_weather_expert
import travel_assistant

# Also use existing A2A agents
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")
ticket_agent = agent(url="http://localhost:5003")

# Create module agents
weather_module_agent = agent(module=advanced_weather_expert)
travel_module_agent = agent(module=travel_assistant)

print("=== Sequential Multi-Agent Collaboration ===")

# Step 1: Weather Analysis (A2A Agent)
destination = "Tokyo"
travel_dates = "March 2025"

weather_analysis = weather_agent.solve(f"Analyze weather conditions in {destination} during {travel_dates}")
print(f"Step 1 - Weather Analysis: {weather_analysis}")

# Step 2: Enhanced Weather Planning (Module Agent)
enhanced_weather = weather_module_agent.solve(f"Based on: {weather_analysis}, provide detailed travel weather advice for {destination}")
print(f"Step 2 - Enhanced Weather: {enhanced_weather}")

# Step 3: Travel Planning (Module Agent)
travel_plan = travel_module_agent.solve(f"Create weather-aware travel plan for {destination} considering: {enhanced_weather}")
print(f"Step 3 - Travel Plan: {travel_plan}")

# Step 4: Ticket Booking (A2A Agent)
ticket_info = ticket_agent.solve(f"Find transport and event tickets for {destination}")
print(f"Step 4 - Tickets: {ticket_info}")

# Step 5: Final Integration (Reason Function)
all_agents = [weather_agent, trip_agent, ticket_agent, weather_module_agent, travel_module_agent]
final_plan = reason(f"Integrate all information into final travel plan: Weather: {weather_analysis}, Enhanced: {enhanced_weather}, Plan: {travel_plan}, Tickets: {ticket_info}", agents=all_agents)
print(f"Step 5 - Final Plan: {final_plan}")
```

### Parallel Agent Consultation

**File: `parallel_consultation.na`**
```dana
import advanced_weather_expert
import travel_assistant

# A2A agents
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")

# Module agents  
weather_module_agent = agent(module=advanced_weather_expert)
travel_module_agent = agent(module=travel_assistant)

print("=== Parallel Agent Consultation ===")

# Consult all agents on the same complex topic
consultation_topic = "Plan a 10-day trip to Japan in cherry blossom season"

# Get perspectives from all agents
perspectives = {}

# A2A agents
perspectives["A2A Weather"] = weather_agent.solve(consultation_topic)
perspectives["A2A Trip Planner"] = trip_agent.solve(consultation_topic)

# Module agents
perspectives["Module Weather Expert"] = weather_module_agent.solve(consultation_topic)
perspectives["Module Travel Assistant"] = travel_module_agent.solve(consultation_topic)

# Display all perspectives
print("All Agent Perspectives:")
for agent_name, perspective in perspectives.items():
    print(f"\n{agent_name}:")
    print(f"{perspective[:150]}...")

# Synthesize using reason function with all agents
all_agents = [weather_agent, trip_agent, weather_module_agent, travel_module_agent]
synthesis = reason(f"Synthesize these expert perspectives into a comprehensive plan: {perspectives}", agents=all_agents)
print(f"\nFinal Synthesis: {synthesis}")
```

## Part 6: Agent Pool Management and Discovery

### Dynamic Pool Creation

```dana
# Based on existing patterns but enhanced
import advanced_weather_expert
import travel_assistant

# Create mixed agent pool
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")
weather_module = agent(module=advanced_weather_expert)
travel_module = agent(module=travel_assistant)

print("=== Dynamic Agent Pool Management ===")

# Start with A2A agents
a2a_pool = agent_pool([weather_agent, trip_agent])
print(f"A2A Pool: {a2a_pool.list_agents()}")

# Add module agents
a2a_pool.add_agent(weather_module)
a2a_pool.add_agent(travel_module)
print(f"Mixed Pool: {a2a_pool.list_agents()}")

# Test agent selection with different tasks
tasks = [
    "What's the current weather in Paris?",
    "Plan a detailed 7-day itinerary for Tokyo",
    "Analyze seasonal weather patterns for Europe",
    "Create a budget-friendly travel plan for Southeast Asia"
]

for task in tasks:
    print(f"\nTask: {task}")
    selected_agent = a2a_pool.select_agent(task)
    if selected_agent:
        print(f"Selected: {selected_agent.name}")
        result = selected_agent.solve(task)
        print(f"Result: {result[:100]}...")
    else:
        print("No suitable agent found")
```

### Agent Capability Discovery

```dana
# Enhanced agent discovery building on existing patterns
import advanced_weather_expert
import travel_assistant

# Create comprehensive agent pool
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")
ticket_agent = agent(url="http://localhost:5003")
weather_module = agent(module=advanced_weather_expert)
travel_module = agent(module=travel_assistant)

comprehensive_pool = agent_pool([weather_agent, trip_agent, ticket_agent, weather_module, travel_module])

print("=== Agent Capability Discovery ===")

# Get all agent cards
agent_cards = comprehensive_pool.get_agent_cards()

for agent_name, card in agent_cards.items():
    print(f"\n--- {agent_name} ---")
    print(f"Description: {card.get('description', 'No description')}")
    print(f"Type: {card.get('type', 'Unknown')}")
    
    # Skills analysis
    skills = card.get('skills', [])
    if skills:
        print("Skills:")
        for skill in skills:
            skill_name = skill.get('name', 'Unknown skill')
            skill_desc = skill.get('description', 'No description')
            print(f"  - {skill_name}: {skill_desc}")
    
    # Resource analysis
    resources = card.get('available_resources', [])
    if resources:
        print(f"Available Resources: {', '.join(resources)}")
    
    # Additional metadata
    if 'resource_count' in card:
        print(f"Resource Count: {card['resource_count']}")
```

## Part 7: Advanced Reason Function Patterns

### Resource-Aware Agent Selection

Building on `test_reason_with_resources.na`:

```dana
# Enhanced resource filtering patterns
websearch = use("mcp", url="http://localhost:8880/websearch")

# Create agents
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")

import advanced_weather_expert
weather_module = agent(module=advanced_weather_expert)

print("=== Resource-Aware Agent Selection ===")

# Test 1: Force external agent use (no local resources)
task1 = "What's the weather forecast for next week?"
result1 = reason(task1, agents=[weather_agent, weather_module], resources=[])
print(f"No resources (external only): {result1[:100]}...")

# Test 2: Limited resources (affects agent selection)
task2 = "Find current weather information online"
result2 = reason(task2, agents=[weather_agent, weather_module], resources=["websearch"])
print(f"With websearch: {result2[:100]}...")

# Test 3: Compare different resource configurations
task3 = "Plan weather-aware travel activities"

print("Resource comparison:")
print("No resources:", reason(task3, agents=[weather_agent, trip_agent], resources=[])[:80])
print("With websearch:", reason(task3, agents=[weather_agent, trip_agent], resources=["websearch"])[:80])
```

### Fallback Behavior Analysis

```dana
# Enhanced fallback testing
weather_agent = agent(url="http://localhost:5001")
trip_agent = agent(url="http://localhost:5002")

print("=== Fallback Behavior Analysis ===")

# Test 1: Suitable task for agents
suitable_task = "What's the weather in Tokyo?"
suitable_result = reason(suitable_task, agents=[weather_agent, trip_agent])
print(f"Suitable task: {suitable_result[:100]}...")

# Test 2: Unsuitable task (should fallback to LLM)
unsuitable_task = "Explain quantum mechanics"
unsuitable_result = reason(unsuitable_task, agents=[weather_agent, trip_agent])
print(f"Unsuitable task (LLM fallback): {unsuitable_result[:100]}...")

# Test 3: Empty agent list
empty_result = reason("What is the capital of France?", agents=[])
print(f"Empty agents (LLM): {empty_result[:100]}...")

# Test 4: Failed agent connection (simulated)
try:
    failed_agent = agent(url="http://localhost:9999", timeout=5)  # Non-existent
    failed_result = reason("Test query", agents=[failed_agent])
    print(f"Failed connection (fallback): {failed_result[:100]}...")
except Exception as e:
    print(f"Connection error handled: {str(e)[:50]}...")
```

## Part 8: Production Patterns and Best Practices

### Error Handling and Resilience

```dana
# Production-ready error handling
print("=== Production Error Handling ===")

# Robust agent creation with error handling
def create_agent_safely(url: str, name: str) -> object:
    try:
        return agent(url=url, timeout=10)
    except Exception as e:
        log(f"Failed to create {name} agent: {e}")
        return None

# Create agents with error handling
weather_agent = create_agent_safely("http://localhost:5001", "Weather")
trip_agent = create_agent_safely("http://localhost:5002", "Trip")
ticket_agent = create_agent_safely("http://localhost:5003", "Ticket")

# Filter out failed agents
available_agents = []
if weather_agent != None:
    available_agents.append(weather_agent)
if trip_agent != None:
    available_agents.append(trip_agent)
if ticket_agent != None:
    available_agents.append(ticket_agent)

print(f"Available agents: {len(available_agents)}")

# Robust reasoning with fallback
def robust_reason(task: str, agents: list) -> str:
    if len(agents) == 0:
        log("No agents available, using LLM fallback")
        return reason(task)
    
    try:
        return reason(task, agents=agents)
    except Exception as e:
        log(f"Agent reasoning failed: {e}, falling back to LLM")
        return reason(task)

# Test robust reasoning
test_task = "Plan a trip to Paris"
result = robust_reason(test_task, available_agents)
print(f"Robust result: {result[:100]}...")
```

### Performance Monitoring

```dana
# Performance monitoring patterns
import time

print("=== Performance Monitoring ===")

# Time different approaches
def time_operation(operation_name: str, operation):
    start_time = time.time()
    result = operation()
    end_time = time.time()
    duration = end_time - start_time
    print(f"{operation_name}: {duration:.2f}s")
    return result

# Create agents for testing
weather_agent = agent(url="http://localhost:5001")
import advanced_weather_expert
weather_module = agent(module=advanced_weather_expert)

test_task = "What's the weather in Tokyo?"

# Compare performance
a2a_result = time_operation("A2A Agent", lambda: weather_agent.solve(test_task))
module_result = time_operation("Module Agent", lambda: weather_module.solve(test_task))
reason_result = time_operation("Reason Function", lambda: reason(test_task, agents=[weather_agent]))
llm_result = time_operation("Direct LLM", lambda: reason(test_task))

print("Performance comparison completed")
```

## Part 9: Complete Real-World Example

### Comprehensive Travel Planning System

**File: `travel_planning_system.na`**
```dana
# Complete travel planning system using all patterns
import advanced_weather_expert
import travel_assistant

print("=== Comprehensive Travel Planning System ===")

# Initialize all available agents
def initialize_agents():
    # A2A agents with error handling
    agents = {}
    
    try:
        agents["weather_a2a"] = agent(url="http://localhost:5001", timeout=30)
        print("✓ Weather A2A agent connected")
    except Exception as e:
        print(f"✗ Weather A2A agent failed: {e}")
    
    try:
        agents["trip_a2a"] = agent(url="http://localhost:5002", timeout=30)
        print("✓ Trip A2A agent connected")
    except Exception as e:
        print(f"✗ Trip A2A agent failed: {e}")
    
    try:
        agents["ticket_a2a"] = agent(url="http://localhost:5003", timeout=30)
        print("✓ Ticket A2A agent connected")
    except Exception as e:
        print(f"✗ Ticket A2A agent failed: {e}")
    
    # Module agents (always available)
    agents["weather_module"] = agent(module=advanced_weather_expert)
    agents["travel_module"] = agent(module=travel_assistant)
    print("✓ Module agents created")
    
    return agents

# Travel planning workflow
def plan_comprehensive_trip(destination: str, duration: str, season: str, budget: str):
    agents = initialize_agents()
    
    # Create agent pools by specialty
    weather_agents = []
    travel_agents = []
    
    if "weather_a2a" in agents:
        weather_agents.append(agents["weather_a2a"])
    if "weather_module" in agents:
        weather_agents.append(agents["weather_module"])
    
    if "trip_a2a" in agents:
        travel_agents.append(agents["trip_a2a"])
    if "travel_module" in agents:
        travel_agents.append(agents["travel_module"])
    
    # Step 1: Weather Analysis
    print(f"\n--- Step 1: Weather Analysis for {destination} in {season} ---")
    weather_query = f"Analyze weather conditions and patterns for {destination} during {season} for {duration} trip"
    weather_analysis = reason(weather_query, agents=weather_agents)
    print(f"Weather Analysis: {weather_analysis[:150]}...")
    
    # Step 2: Itinerary Planning
    print(f"\n--- Step 2: Itinerary Planning ---")
    itinerary_query = f"Create detailed {duration} itinerary for {destination} in {season} considering weather: {weather_analysis}"
    itinerary = reason(itinerary_query, agents=travel_agents)
    print(f"Itinerary: {itinerary[:150]}...")
    
    # Step 3: Budget Planning
    print(f"\n--- Step 3: Budget Planning ---")
    budget_query = f"Estimate {budget} budget for {duration} trip to {destination} including accommodation, food, activities, and transport"
    budget_analysis = reason(budget_query, agents=travel_agents)
    print(f"Budget: {budget_analysis[:150]}...")
    
    # Step 4: Ticket Information
    print(f"\n--- Step 4: Ticket Information ---")
    if "ticket_a2a" in agents:
        ticket_query = f"Find transport and event tickets for {destination}"
        ticket_info = agents["ticket_a2a"].solve(ticket_query)
        print(f"Tickets: {ticket_info[:150]}...")
    else:
        ticket_info = "Ticket agent not available"
        print("Tickets: Service unavailable")
    
    # Step 5: Final Integration
    print(f"\n--- Step 5: Final Integration ---")
    all_available_agents = list(agents.values())
    final_query = f"Create comprehensive travel guide for {destination} integrating: Weather: {weather_analysis}, Itinerary: {itinerary}, Budget: {budget_analysis}, Tickets: {ticket_info}"
    final_plan = reason(final_query, agents=all_available_agents)
    print(f"Final Plan: {final_plan[:200]}...")
    
    return {
        "weather": weather_analysis,
        "itinerary": itinerary,
        "budget": budget_analysis,
        "tickets": ticket_info,
        "final_plan": final_plan
    }

# Execute comprehensive planning
result = plan_comprehensive_trip(
    destination="Kyoto, Japan",
    duration="7 days",
    season="spring cherry blossom season",
    budget="mid-range"
)

print("\n=== Travel Planning Complete ===")
print("All components successfully integrated!")
```

## Summary of Dana Agent Capabilities

### ✅ **Complete Feature Set**

1. **A2A Agent Integration**:
   - Weather, Trip Planner, and Ticket agents
   - Robust connection handling
   - Skill-based task routing

2. **Module Agent Creation**:
   - System variable requirements
   - Resource integration
   - Custom solve functions

3. **Reason Function Enhancement**:
   - `agents=` parameter for delegation
   - Resource filtering with `resources=`
   - Intelligent agent selection
   - Automatic fallback to LLM

4. **Agent Pool Management**:
   - Dynamic agent addition/removal
   - Mixed A2A and module agents
   - Capability discovery
   - Performance monitoring

5. **Production Patterns**:
   - Error handling and resilience
   - Performance monitoring
   - Resource-aware selection
   - Comprehensive workflows

### 🚀 **Key Benefits**

- **Unified Interface**: Same API for all agent types
- **Intelligent Selection**: LLM-based agent selection
- **Resource Awareness**: Agents know their capabilities
- **Fallback Mechanisms**: Graceful failure handling
- **Production Ready**: Comprehensive error handling

This guide demonstrates Dana's world-class multi-agent architecture, building upon the solid foundation in `examples/dana/08_a2a_multi_agents/` to create sophisticated, production-ready multi-agent systems! 🎉
