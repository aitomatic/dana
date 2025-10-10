# Phase 1: Agent Examples

This directory contains examples demonstrating the core agent capabilities and multi-agent communication features of the Adana framework, including:

## Examples

### 1. Basic Agent Example (`agent_example.py`)
- **Single Agent**: Basic agent functionality with Timeline integration
- **Resource Integration**: Mock resource and workflow registration
- **Timeline Tracking**: Complete conversation history management
- **Live Mode**: Real LLM integration with error handling

### 2. STAR Agent Example (`star_agent_example.py`) ⭐ NEW
- **STAR Pattern**: See-Think-Act-Reflect decision making
- **Direct System Prompts**: Hardcoded system prompt generation
- **XML Tool Calls**: Structured tool calling format
- **Interactive Mode**: Chat-like conversation interface
- **Timeline Management**: Conversation history tracking

### 3. STAR Multi-Agent Example (`star_multi_agent_example.py`) ⭐ NEW
- **Multiple STARAgents**: Different specialized agents
- **Agent Discovery**: Automatic agent registration and discovery
- **Agent Communication**: Direct agent-to-agent messaging
- **STAR Pattern**: Each agent uses See-Think-Act-Reflect
- **Coordinated Decision Making**: Multi-agent collaboration

### 4. Multi-Agent Communication Example (`multi_agent_example.py`)
This example demonstrates the multi-agent communication capabilities, including:

- **Agent Registry**: Centralized agent discovery and management
- **Agent-to-Agent Messaging**: Direct communication between agents
- **Timeline Tracking**: Comprehensive conversation history across all interactions
- **Specialized Agents**: Different agent types with unique capabilities
- **Resource Integration**: Agents with specific resources and workflows

## Features Demonstrated

### 1. Agent Registration and Discovery
- Automatic agent registration with the global registry
- Agent discovery by type and capability
- Agent information retrieval and management

### 2. Multi-Agent Communication
- Direct agent-to-agent messaging
- Message queuing and delivery
- Error handling for invalid agents

### 3. Timeline Integration
- All agent interactions tracked in timeline
- Context preservation across agent communications
- Rich metadata for debugging and analysis

### 4. Specialized Agent Types
- **Coding Agent**: Code analysis, debugging, test generation
- **Financial Agent**: Market analysis, risk assessment
- **Research Agent**: Data collection, report generation
- **Coordinator Agent**: Project coordination and management

## Usage

### Basic Agent Example
```bash
# Simulated mode (no LLM calls)
python agent_example.py

# Live mode (actual LLM calls)
python agent_example.py --live

# With specific provider
python agent_example.py --live --provider anthropic --model claude-3-haiku
```

### STAR Agent Example ⭐ NEW
```bash
# Simulated mode (no LLM calls)
python star_agent_example.py

# Live mode (actual LLM calls)
python star_agent_example.py --live

# With specific provider
python star_agent_example.py --live --provider openai
python star_agent_example.py --live --provider anthropic --model claude-3-haiku
```

### STAR Multi-Agent Example ⭐ NEW
```bash
# Simulated mode (no LLM calls)
python star_multi_agent_example.py

# Live mode (actual LLM calls)
python star_multi_agent_example.py --live

# With specific provider
python star_multi_agent_example.py --live --provider openai
python star_multi_agent_example.py --live --provider anthropic --model claude-3-haiku
```

### Multi-Agent Communication Example
```bash
# Simulated mode (no LLM calls)
python multi_agent_example.py

# Live mode (actual LLM calls)
python multi_agent_example.py --live

# With specific provider
python multi_agent_example.py --live --provider openai
python multi_agent_example.py --live --provider anthropic --model claude-3-haiku
```

## Example Scenarios

### Scenario 1: Agent Discovery
The coordinator agent discovers all available agents and their capabilities.

### Scenario 2: Direct Communication
Coordinator asks specialized agents for help with specific tasks.

### Scenario 3: Multi-Agent Collaboration
Multiple agents work together on a complex project, with the coordinator orchestrating the workflow.

### Scenario 4: Timeline Tracking
All interactions are tracked in each agent's timeline, providing complete audit trails.

## Architecture

```
Coordinator Agent
├── Discovers other agents
├── Routes messages between agents
└── Maintains project context

Specialized Agents
├── Coding Agent (Python, debugging, testing)
├── Financial Agent (Market analysis, risk assessment)
├── Research Agent (Data collection, reports)
└── Each with unique resources and workflows

Agent Registry
├── Centralized agent management
├── Message routing and queuing
└── Agent discovery and status tracking

Timeline System
├── Unified conversation history
├── Token-aware context management
└── Rich metadata and debugging info
```

## Agent Implementations

### Deprecated Agent (`adana.core.agent.agent`)
- **Status**: Deprecated (has bugs)
- **System Prompts**: Uses PromptEngineer (currently broken)
- **Decision Pattern**: Iterative See-Think-Act
- **Tool Calls**: Multiple formats (XML, structured, markdown)
- **Issues**: 
  - `get_context_for_llm()` method doesn't exist
  - PromptEngineer references `object` instead of `agent`
  - System prompts are empty due to bugs

### STAR Agent (`adana.core.agent.star_agent`) ⭐ RECOMMENDED
- **Status**: Active and working
- **System Prompts**: Direct hardcoded generation
- **Decision Pattern**: STAR (See-Think-Act-Reflect)
- **Tool Calls**: XML format only
- **Features**:
  - Working system prompt generation
  - STAR pattern implementation
  - Interactive conversation mode
  - Agent-to-agent communication
  - Timeline management

## Key Components

### Agent Registry (`adana.core.agent.registry`)
- `AgentRegistry`: Centralized agent management
- `AgentInfo`: Agent metadata and capabilities
- Message queuing and delivery
- Agent discovery and filtering

### Enhanced Agent Class
- Automatic registry integration
- Agent discovery methods
- Direct agent-to-agent communication
- Timeline-based context management

### Timeline Integration
- All agent interactions tracked
- Context preservation across communications
- Rich debugging and analysis capabilities

## Testing

Run the comprehensive test suite:

```bash
pytest tests/integration/test_multi_agent_communication.py -v
```

## Benefits

1. **Scalable Architecture**: Easy to add new agent types and capabilities
2. **Unified Communication**: Single interface for all agent interactions
3. **Rich Context**: Timeline preserves all conversation history
4. **Flexible Discovery**: Find agents by type, capability, or other criteria
5. **Error Handling**: Robust error handling and recovery
6. **Debugging**: Complete audit trail of all interactions

## Future Enhancements

- **Message Persistence**: Save/load message queues
- **Agent Clustering**: Group agents by project or domain
- **Load Balancing**: Distribute messages across multiple agents
- **Message Routing**: Intelligent routing based on agent capabilities
- **Real-time Updates**: WebSocket-based real-time communication
