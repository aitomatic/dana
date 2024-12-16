<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Agent System

The agent system provides the core implementation of DXA agents, handling configuration, execution, and state management.

## Core Concepts

### Agent Components

An Agent in DXA is composed of:

1. A cognitive core (Reasoning) for decision-making
2. Capabilities that define its abilities
3. Resources it can access
4. I/O channels for interaction

### Key Components

1. **Agent** - The high-level interface that:
   - Provides the fluent configuration API
   - Manages component lifecycle
   - Delegates task execution to Runtime
   - Maintains agent identity and configuration

2. **AgentRuntime** - The execution environment that:
   - Manages execution state and context
   - Coordinates resource access
   - Tracks progress and handles errors
   - Provides the execution loop

3. **BaseReasoning** - The cognitive engine that:
   - Implements decision-making logic
   - Processes tasks through defined patterns
   - Manages reasoning state
   - Interacts with capabilities and resources

## System Structure

### State Management

- **Agent** holds configuration state
- **AgentRuntime** manages execution state
- **BaseReasoning** maintains reasoning context

### Component Integration

```python
# Configuration state
agent = Agent("researcher")\
    .with_reasoning("cot")\
    .with_resources({"llm": my_llm})

# Execution state
async with agent.runtime.execution_context() as ctx:
    # Reasoning state
    result = await agent.reasoning.reason_about(task, ctx)
```

## Execution Flow

### Task Processing

When you call `agent.run(task)`:

1. **Agent** prepares the execution:

   ```python
   result = await agent.run(task)
   # - Validates configuration
   # - Creates execution context
   # - Delegates to runtime
   ```

2. **AgentRuntime** manages the process:

   ```python
   async def execute(self, task: Task) -> Result:
       # - Initializes state
       # - Sets up resources
       # - Delegates to reasoning
       # - Handles errors and cleanup
   ```

3. **BaseReasoning** performs the work:

   ```python
   async def reason_about(self, task: Task, context: Context) -> Result:
       # - Applies reasoning pattern
       # - Uses capabilities
       # - Accesses resources
       # - Returns results
   ```

### Usage Examples

#### Basic Usage

```python
from dxa.agent import Agent
from dxa.core.resource import LLMResource

# Create simple agent
agent = Agent("assistant")\
    .with_reasoning("cot")\
    .with_resources({"llm": LLMResource(model="gpt-4")})

# Run task
result = await agent.run("Analyze this data")
```

#### Advanced Configuration

```python
from dxa.agent import Agent, AgentConfig
from dxa.core.capability import MemoryCapability

agent = Agent(
    name="analyst",
    config=AgentConfig(
        reasoning_level="ooda",
        max_iterations=10,
        temperature=0.7
    )
)\
.with_capabilities([
    MemoryCapability(size=1000),
    "planning",
    "research"
])
```

## Development

### Creating Custom Agents

1. Extend base Agent class:

```python
class CustomAgent(Agent):
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.custom_setup()

    async def custom_setup(self):
        """Add custom initialization"""
        pass
```

### Best Practices

1. State Management

- Use AgentState for persistent data
- Keep runtime state in context
- Clean up resources properly

1. Error Handling

- Implement graceful degradation
- Provide meaningful error messages
- Log important state changes

1. Testing

- Test with different reasoning patterns
- Verify resource interaction
- Check error conditions

### API Reference

```python
class Agent:
    """Main agent interface."""
    
    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        """Initialize agent with name and optional config."""
        
    def with_reasoning(self, reasoning: Union[str, BaseReasoning]) -> "Agent":
        """Configure reasoning system."""
        
    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources to agent."""
        
    def with_capabilities(self, capabilities: List[Union[str, BaseCapability]]) -> "Agent":
        """Add capabilities to agent."""
        
    async def run(self, task: Union[str, Dict[str, Any]]) -> Any:
        """Execute task and return result."""
```

See individual module documentation for detailed API references.
