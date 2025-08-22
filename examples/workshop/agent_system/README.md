# System of Agents Demo

This directory demonstrates a multi-agent system built with Dana, featuring a General-Management Agent (GMA) that orchestrates specialist agents to accomplish complex tasks.

## Prerequisites

```bash
cd examples/dana/202506_workshop/2_agent_and_system_of_agents/system_of_agents
```

## How to Run the Demo

### Multi-Agent

For multi-agent scenarios, agents are **imported**.

```bash
dana gma.na
```

This will run the General-Management Agent, which automatically imports and coordinates multiple specialist agents:
- Weather Agent (specialist_agent_1.na) - imported as module
- Search Agent (specialist_agent_2.na) - imported as module  
- Flight Agent (specialist_agent_3.na) - imported as module

All agents work together within the same process, sharing context and coordinating seamlessly.

### Explore Multi-Agent Syntax (Optional)

To understand different patterns of multi-agent interaction:

```bash
dana multi_agent_syntax.na
```

## File Descriptions

### Core Agent Files

#### `gma.na` - General-Management Agent
- **Purpose**: Main orchestration agent that manages a team of specialist agents
- **Functionality**: 
  - Creates an agent pool with weather, search, and ticketing agents
  - Plans complex tasks by breaking them into steps
  - Executes plans by coordinating specialist agents
  - Demonstrates both local module-based agents
- **Example Task**: Plans a trip to Tokyo by coordinating weather, search, and flight booking agents

#### `specialist_agent_1.na` - Weather Reporter/Forecaster
- **Purpose**: Provides current and forecast weather information
- **Resources**: Uses MCP (Model Context Protocol) weather service at `http://127.0.0.1:8000/mcp`
- **Functionality**: Answers weather-related queries with date awareness

#### `specialist_agent_2.na` - Web Searcher
- **Purpose**: Answers questions by searching the web
- **Resources**: Uses MCP web search service at `https://demo.mcp.aitomatic.com/websearch_v2`
- **Functionality**: Performs web searches to find information

#### `specialist_agent_3.na` - Flight Ticket Agent - COMPLEX WORKFLOW
- **Purpose**: Finds the best flight tickets based on requests
- **Resources**: Uses MCP web search service for flight information
- **Functionality**: 
  - Creates plans for flight ticket searches
  - Executes searches iteratively until satisfactory results are found

### Demo and Reference Files

#### `multi_agent_syntax.na` - Multi-Agent Syntax Examples
- **Purpose**: Demonstrates different patterns for using multiple agents
- **Patterns Shown**:
  1. Direct agent usage (`agent.solve()`)
  2. Agent pool with automatic selection (`pool.select_agent()`)
  3. Implicit agent pool with reasoning (`reason(..., agents=[...])`)

#### `py/reference.md` - External Reference
- **Purpose**: Links to LangGraph multi-agent tutorial for additional learning
- **Content**: Reference to LangChain's agent supervisor tutorial

## Key Concepts Demonstrated

### Agent Types
1. **Module-based Agents**: Imported from Dana modules (specialist_agent_1, specialist_agent_2, specialist_agent_3)
2. **Agent Pools**: Collections of agents that can be automatically selected based on task requirements

### Multi-Agent Patterns
- **Orchestration**: GMA coordinates multiple specialist agents
- **Pipeline Processing**: Tasks are broken into steps and executed sequentially
- **Resource Sharing**: Agents use external resources via MCP
- **Automatic Agent Selection**: System selects appropriate agents based on task context

### Dana Features Showcased
- Agent card declarations with names and descriptions
- Resource integration with MCP services
- Workflow composition using pipelines (`plan | execute`)
- Agent coordination and data exchange
- JSON handling for structured data exchange

## Architecture Overview

```
General-Management Agent (gma.na)
├── Weather Agent (specialist_agent_1.na) → MCP Weather Service
├── Search Agent (specialist_agent_2.na) → MCP Web Search
└── Flight Agent (specialist_agent_3.na)
```

The system demonstrates how Dana enables seamless integration of multiple agents, automatic task planning, and coordinated execution across specialized capabilities.
