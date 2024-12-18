<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
    <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Agents

This directory contains the core agent implementations for the DXA framework. Each agent type is specialized for different interaction patterns and execution models.

## Class Hierarchy

```text
BaseAgent
├── AutonomousAgent        # Independent operation
├── InteractiveAgent      # User interaction
├── WebSocketAgent        # Network communication
├── WorkAutomationAgent   # Workflow automation
└── CollaborativeAgent    # Multi-agent coordination
```

## Agent Types

### BaseAgent

Abstract base class providing common functionality:

- Resource management
- Error handling
- Default Chain of Thought reasoning
- Progress tracking
- State management

### AutonomousAgent

Specialized for independent operation:

- Runs without user interaction
- Stricter validation of task parameters
- Detailed progress reporting
- Automatic handling of stuck states

### InteractiveAgent

Enables real-time user interaction:

- Console-based interaction
- Progress monitoring
- Decision points
- User feedback collection
- Flow control (continue/stop)

### WebSocketAgent

Network-based agent using WebSocket communication:

- Bidirectional communication
- Connection state management
- Reconnection handling
- Message serialization
- Error recovery

### WorkAutomationAgent

Focused on workflow automation:

- Step-by-step execution
- Process validation
- Retry mechanisms
- State tracking
- Default OODA-loop reasoning

### CollaborativeAgent

Enables multi-agent coordination:

- Agent-to-agent communication
- Task delegation
- Result aggregation
- Collaboration history tracking
- Resource sharing

## Supporting Components

### StateManager

Manages agent state and execution history:

- Observations
- Messages
- Working memory
- State transitions

### AgentProgress

Reports task progress and results:

- Progress updates
- Completion status
- Error reporting
- Result formatting

### AgentLLM

Agent-specific LLM implementation:

- Prompt management
- Context handling
- Response formatting
- Agent-specific configurations

### Configuration

Configuration management through:

- `LLMConfig`: LLM-specific settings

## Usage Example

```python
from dxa.agent import InteractiveAgent
from dxa.core.reasoning import ChainOfThoughtReasoning

# Create an interactive agent
agent = InteractiveAgent(
    name="math_tutor",
    llm_config={
        "model": "gpt-4",
        "temperature": 0.7
    },
    reasoning=ChainOfThoughtReasoning(),
    description="Interactive math tutoring agent"
)

# Run with progress updates
async for progress in agent.run_with_progress({
    "objective": "teach_algebra",
    "topic": "quadratic_equations"
}):
    if progress.is_progress:
        print(f"Progress: {progress.percent}% - {progress.message}")
    elif progress.is_result:
        print("Final result:", progress.result)
```

## Directory Structure

```text
agent/
├── __init__.py              # Package exports
├── agent_llm.py             # Agent-specific LLM implementation
├── agent_progress.py        # Progress reporting
├── agent_runtime.py         # Execution runtime
├── agent_state.py           # State management
├── autonomous_agent.py      # Autonomous agent implementation
├── base_agent.py            # Base agent class
├── collaborative_agent.py   # Multi-agent coordination
├── config.py                # Configuration classes
├── interactive_agent.py     # Interactive agent implementation
├── websocket_agent.py       # WebSocket-based agent
└── work_automation_agent.py # Workflow automation agent
```
