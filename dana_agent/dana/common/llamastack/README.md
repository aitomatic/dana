# LlamaStack Integration

This module provides integration with LlamaStack's APIs. We:

- (located in common/llm/llamastack.py) **USE** LlamaStack's Inference API
- **USE** LlamaStack's Conversation API (convert to our Timeline)
- **USE** LlamaStack's Storage API (convert to our Resources)
- **PROVIDE** a plugin for LlamaStack's Agent API

## Providing Agent API Plugin

To provide a plugin for LlamaStack's Agent API, you need to:

1. **Create an HTTP endpoint** that LlamaStack can call
2. **Register your endpoint** with LlamaStack (via configuration or API)

Here's an example using FastAPI:

```python
from fastapi import FastAPI, HTTPException
from dana.common.llamastack import LlamaStackAgentAPI
from dana.core.agent.star_agent import STARAgent

app = FastAPI()

# Create your STARAgent
star_agent = STARAgent(agent_type="hvac", agent_id="hvac-agent-001")

# Create the LlamaStack Agent API plugin
agent_api = LlamaStackAgentAPI(star_agent=star_agent)

@app.post("/llamastack/agent/decide")
async def agent_decide(context: dict):
    """
    LlamaStack will call this endpoint when it needs an agent decision.

    This endpoint receives LlamaStack's context and returns a decision.
    """
    try:
        decision = await agent_api.decide(context)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Register with LlamaStack
# Option 1: Via LlamaStack config file
# agent_providers:
#   - name: "dana-agent"
#     endpoint: "http://localhost:8000/llamastack/agent/decide"
#     type: "http"

# Option 2: Via LlamaStack API (if supported)
# await llamastack_client.agents.register_provider(
#     name="dana-agent",
#     endpoint="http://localhost:8000/llamastack/agent/decide"
# )
```

## How It Works

### Plugin Flow

```
LlamaStack Agent Workflow
    ↓
Needs agent decision
    ↓
HTTP POST → /llamastack/agent/decide
    ↓
LlamaStackAgentAPI.decide(context)
    ↓
Converts context → STARAgent input format
    ↓
STARAgent.query(**agent_input)
    ↓
STAR loop execution (See → Think → Act → Reflect)
    ↓
Converts agent output → LlamaStack decision format
    ↓
HTTP Response ← Decision
    ↓
LlamaStack continues workflow
```

### Context Format

LlamaStack sends context like:

```json
{
  "session_id": "session-123",
  "goal": "Control HVAC zone temperature",
  "environment": {
    "zone": "floor_2_west",
    "temp": 72.5,
    "setpoint": 72
  },
  "history": [...],
  "tools": ["adjust_temperature", "check_occupancy"]
}
```

We convert this to STARAgent input, run through STAR loop, and return:

```json
{
  "action": "execute_tools",
  "reasoning": "Zone temp is above setpoint, need to cool",
  "confidence": 0.9,
  "next_state": {...},
  "tool_calls": [...]
}
```

## Configuration

Set the LlamaStack base URL in your config or environment:

```bash
export LLAMA_STACK_URL=http://localhost:8321
```

Or in `config.json`:

```json
{
  "llm": {
    "providers": {
      "llamastack": {
        "base_url": "http://localhost:8321"
      }
    }
  }
}
```
