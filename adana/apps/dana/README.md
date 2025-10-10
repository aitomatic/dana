# Dana - Conversational AI Coordinator

Dana is a conversational AI agent that helps you manage and orchestrate a multi-agent system through natural language interaction.

## Overview

Instead of writing code or issuing commands, you simply talk to Dana about what you want to accomplish. Dana will:
- Create and manage specialized agents
- Execute workflows and access resources
- Coordinate complex multi-agent operations
- Provide status updates and information

## Usage

### Start Dana

```bash
# Using the adana command
adana

# Or using Python module
uv run python -m adana.apps.dana
```

### Example Conversation

```
╔═══════════════════════════════════════════════════════════╗
║  Dana - Your AI Coordinator                               ║
╚═══════════════════════════════════════════════════════════╝

Hi! I'm Dana, your conversational AI coordinator.

You: What agents do I have available?

🤖 Dana: You currently have 4 agents available:
  • research-agent: Specializes in information gathering
  • analysis-agent: Specializes in data interpretation
  • verifier-agent: Specializes in quality assurance
  • coordinator-agent: Manages multi-agent operations

Would you like to use one of these agents or create a new one?

You: I need to research renewable energy trends

🤖 Dana: I'll ask the research agent to investigate renewable energy trends.
Let me coordinate that for you...

[Dana delegates to research agent]

🤖 Dana: The research agent has completed the investigation. Here are the key findings:
[response from research agent]

Would you like me to have the analysis agent review these findings?

You: Yes, please analyze the trends

🤖 Dana: I'll coordinate with the analysis agent to review the findings...
```

## Commands

Dana supports special commands starting with `/`:

- `/help` - Show available commands
- `/agents` - List all available agents
- `/resources` - List all available resources
- `/workflows` - List all available workflows
- `/status` - Show Dana's current status
- `/reset` - Reset conversation history
- `/exit` - Exit Dana

## Features

### Natural Conversation
Just talk to Dana naturally about what you need. No code or complex syntax required.

### Agent Management
Dana can create, list, and manage specialized agents:
- ResearchAgent: Information gathering and analysis
- AnalysisAgent: Data interpretation and insights
- VerifierAgent: Quality assurance and validation
- CoordinatorAgent: Multi-agent task coordination
- Custom agents on request

### Resource Access
Dana has access to resources like:
- ToDoResource: Task tracking and management
- And more as you need them

### Workflow Execution
Dana can execute workflows to accomplish complex tasks through conversation.

## Architecture

```
User Conversation
      ↓
Dana Agent (STARAgent)
      ↓
┌─────┴─────────────────┐
│                       │
Specialized Agents   Resources & Workflows
```

Dana is built on top of STARAgent (See-Think-Act-Reflect) which provides:
- **See**: Observes and understands your requests
- **Think**: Analyzes and plans the best approach
- **Act**: Executes actions via agents/resources/workflows
- **Reflect**: Learns from outcomes to improve

## Key Files

- `dana_agent.py` - DanaAgent implementation (STARAgent subclass)
- `dana_app.py` - Conversational UI with prompt_toolkit
- `__main__.py` - Entry point

## Comparison: Dana vs REPL

| Feature | Dana (adana) | REPL (adana-repl) |
|---------|--------------|-------------------|
| **Interface** | Natural conversation | Python code |
| **Use Case** | Task-oriented interaction | Programming/scripting |
| **Learning Curve** | None (just talk) | Requires Python knowledge |
| **Agent Management** | Conversational | Programmatic |
| **Best For** | End users, quick tasks | Developers, scripting |

## Example Use Cases

### Research Task
```
You: I need to research quantum computing applications in healthcare

🤖 Dana: I'll coordinate with the research agent to investigate that...
```

### Multi-Agent Coordination
```
You: I need a comprehensive analysis of market trends with verification

🤖 Dana: I'll coordinate a multi-step process:
1. Research agent will gather market data
2. Analysis agent will identify trends
3. Verifier agent will validate findings

Let me get started...
```

### System Management
```
You: What's the status of all agents?

🤖 Dana: Here's the current status:
[Shows detailed status of all agents, resources, and workflows]
```

## Tips

1. **Be conversational**: Just talk naturally to Dana
2. **Ask for help**: Dana can explain what it can do
3. **Request specific agents**: Ask Dana to create or use specific agent types
4. **Check status**: Use `/status` to see system information
5. **Use commands**: Commands like `/agents` provide quick information

## Technical Details

- **Built on**: STARAgent framework
- **UI**: prompt_toolkit for interactive prompts
- **Pre-configured**: Access to research, analysis, verifier, and coordinator agents
- **Extensible**: Can create new agents dynamically based on needs

## Next Steps

- Try conversing with Dana: `adana`
- For Python scripting: `adana-repl`
- See example conversations in the examples directory