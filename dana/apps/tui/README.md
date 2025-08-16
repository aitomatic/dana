# Dana Multi-Agent REPL TUI

A modern terminal user interface for interacting with multiple Dana agents simultaneously. Built with [Textual](https://textual.textualize.io/) for a snappy, responsive experience.

![Dana TUI Screenshot](docs/screenshot.png)

## Features

- **Multi-Agent Support**: Create, manage, and interact with multiple agents
- **Real-time Streaming**: See agent responses as they generate (token streaming)
- **Thinking Feed**: Watch agent reasoning in real-time with step-by-step breakdowns
- **Task Management**: Cancel individual or all running tasks with `Esc`/`Shift+Esc`
- **Smart Routing**: Route commands to specific agents with `@agent` syntax
- **Rich Interface**: Modern TUI with syntax highlighting and visual feedback

## Quick Start

### Installation

```bash
# Install textual if not already installed
pip install textual>=0.58

# Run from the Dana project root
python -m dana.tui
# OR run the REPL-style app directly
python -m dana.tui.repl_style_app
```

### Basic Usage

1. **Start the TUI**: `python -m dana.tui`
2. **Create an agent**: `agent myagent`
3. **Send a message**: `Hello, how are you?`
4. **Route to specific agent**: `@research find papers on AI`
5. **Get help**: `:help`

## Layout

The TUI features a clean two-panel layout with a simple terminal-like interface:

```
┌─────────────────────────────────┬──────────────────────┐
│ Terminal                        │ Agents               │
│                                 │ → ● research  step:  │
│ >>> 5 + 3                       │   ○ coder     idle   │
│ 8                               │   ○ planner   idle   │
│                                 │                      │
│ >>> agent newagent              │ Agent Detail         │
│ Created agent 'newagent'        │ research • analyzing │
│                                 │ 14:32:15 STATUS:     │
│ >>> @research find AI papers    │   analyzing query    │
│ → Routing to research: find AI  │ 14:32:16 TOOL→:      │
│                                 │   search {"query":   │
│ >>> █                           │ 14:32:17 TOOL✓:      │
│                                 │   search [OK] 250ms  │
└─────────────────────────────────┴──────────────────────┘
```

### Panel Details

- **LEFT Panel (65%)**: Simple terminal with inline command input and output, just like a Unix terminal
- **RIGHT Panel (35%)**: 
  - **Top**: Real-time agent list with status and metrics
  - **Bottom**: Detailed agent I/O and thinking feed

## Command Reference

### Agent Management
- `agent <name>` - Create new agent
- `@<agent> <message>` - Send message to specific agent  
- `<agent>.chat("message")` - Call agent's chat method directly

### Meta Commands
- `:agents` - List all agents
- `:use <name>` - Focus on agent
- `:new <name>` - Create agent (alias for `agent`)
- `:kill <name>` - Remove agent
- `:clear` - Clear transcript
- `:help` - Show help
- `:quit` - Exit application

### Navigation & Control
- `Tab` / `Shift+Tab` - Navigate between agents
- `Enter` (in agent list) - Focus selected agent
- `Esc` - Cancel focused agent's current task
- `Shift+Esc` - Cancel all running tasks
- `F1` - Show help
- `Ctrl+L` - Clear transcript  
- `Ctrl+S` - Save logs (not yet implemented)
- `Ctrl+C` - Quit application

## Performance Features

- **Token Coalescing**: Buffers tokens and flushes every 40-80ms for smooth streaming
- **Update Throttling**: Side panels update at 1-2Hz to avoid UI churn
- **Non-blocking**: All agent operations run asynchronously
- **Fast Cancellation**: Tasks cancel within ≤150ms

## Architecture

```
dana/tui/
├── __init__.py              # Package initialization and main entry point
├── __main__.py              # Module execution entry point (python -m dana.tui)
├── repl_style_app.py        # Main REPL-style TUI (default)
├── app.py                   # Legacy multi-panel TUI
├── core/
│   ├── events.py           # Event types (Token, Status, etc.)
│   ├── runtime.py          # Agent & DanaSandbox
│   ├── mock_agents.py      # Demo agents
│   ├── router.py           # Command parsing & routing
│   └── taskman.py          # Task management & cancellation
└── ui/
    ├── agents_list.py      # Agent list widget
    ├── repl_panel.py       # REPL with transcript & input
    └── agent_detail.py     # Thinking feed display
```

## Extending with Real Dana Agents

To integrate with real Dana agents:

1. **Implement the Agent interface**:
```python
from dana.tui.core.runtime import Agent
from dana.tui.core.events import *

class MyDanaAgent(Agent):
    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        # Your agent implementation
        yield Status("thinking", "Processing request")
        # ... tool calls, progress, tokens ...
        yield FinalResult({"status": "success"})
        yield Done()
```

2. **Register in the sandbox**:
```python
from dana.tui import DanaSandbox

sandbox = DanaSandbox()
sandbox.register(MyDanaAgent("myagent"))
```

3. **Connect to Dana core**:
```python
# In your agent's chat method, integrate with Dana's execution engine
async def chat(self, message: str):
    # Use Dana's interpreter, LLM calls, etc.
    # Yield appropriate events as execution progresses
```

## Development

### Running Tests
```bash
cd dana/tui
python -m pytest tests/ -v
```

### Code Structure
- **Events**: All agent communication flows through typed events
- **Async**: Heavy use of asyncio for non-blocking operations  
- **Reactive UI**: Textual reactive widgets update automatically
- **Separation**: Core logic independent of UI layer

### Adding New Features
1. Define events in `core/events.py`
2. Update agents to emit new events
3. Handle events in UI components
4. Add tests for new functionality

## Troubleshooting

### Common Issues

**"No agent focused"**
- Create an agent first: `agent myagent`
- Or focus existing agent: `:use research`

**Slow performance**
- Check if you have many long-running tasks
- Use `Shift+Esc` to cancel all tasks

**Tasks not cancelling**
- Make sure agents properly handle `asyncio.CancelledError`
- Check that cancel tokens are being respected

### Debug Mode
```bash
# Run with debug logging
TEXTUAL_LOG=debug python -m dana.tui
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation
4. Ensure responsive performance (1-2Hz updates max)

## License

Copyright © 2025 Aitomatic, Inc.  
MIT License - see LICENSE file for details.

## Community

- **GitHub**: https://github.com/aitomatic/dana
- **Discord**: https://discord.gg/6jGD4PYk
- **Website**: https://aitomatic.com
