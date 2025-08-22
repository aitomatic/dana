# LangGraph Reasoning Agent - A2A Deployment

This directory contains the A2A (Agent-to-Agent) deployment for the LangGraph Reasoning Agent, allowing it to be deployed as a service for inter-agent communication.

## Files

- `reasoning_agent_langgraph_fixed.py` - The core LangGraph reasoning agent implementation
- `deploy_reasoning_agent_a2a.py` - A2A deployment script
- `test_reasoning_agent_a2a.py` - Test client for the A2A service
- `README_A2A.md` - This documentation

## Prerequisites

1. **Python Dependencies**
   ```bash
   pip install python-a2a langgraph langchain-openai langchain-mcp-adapters
   ```

2. **Environment Setup**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Optional: MCP Server** (for weather tools)
   - Run an MCP server on `http://localhost:8000/mcp/` 
   - The agent will work without it but won't have weather capabilities

## Quick Start

### 1. Deploy the A2A Agent

```bash
# Start the A2A service on default port 5002
python deploy_reasoning_agent_a2a.py

# Or with custom settings
python deploy_reasoning_agent_a2a.py --host 0.0.0.0 --port 8080 --debug
```

The service will be available at:
- **A2A Endpoint**: `http://localhost:5002/a2a`
- **Health Check**: `http://localhost:5002/health`

### 2. Run the Agent

```bash
# Run the agent to test out the logic
python reasoning_agent_langgraph_fixed.py
```
