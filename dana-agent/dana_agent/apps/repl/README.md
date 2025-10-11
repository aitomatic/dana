# Adana REPL

A streamlined interactive Python REPL with pre-imported Adana classes and enhanced features.

## Features

- **Pre-imported Adana classes**:
  - Core: BaseAgent, BaseSTARAgent, STARAgent, BaseWorkflow, BaseResource
  - Example Agents: ResearchAgent, AnalysisAgent, VerifierAgent, CoordinatorAgent
  - Resources: ToDoResource
  - Workflows: ExampleWorkflow
- **Pre-instantiated objects** (ready to use):
  - `research_agent` - ResearchAgent instance
  - `analysis_agent` - AnalysisAgent instance
  - `verifier_agent` - VerifierAgent instance
  - `coordinator_agent` - CoordinatorAgent instance (wired with other agents)
  - `todo_resource` - ToDoResource instance
  - `example_workflow` - ExampleWorkflow instance
- **Syntax highlighting**: Powered by `prompt_toolkit` and `pygments`
- **Command history**: Navigate previous commands with arrow keys
- **Multi-line input**: Automatic detection for statements ending with `:` or `\`
- **Async/await support**: Use `await` directly for coroutines
- **Special commands**: `/help`, `/imports`, `/exit`

## Installation

The REPL is included with Adana. For enhanced features (syntax highlighting, history), install with dev dependencies:

```bash
# Full features with prompt-toolkit
uv sync --all-extras

# Or minimal (uses standard input, no syntax highlighting)
uv sync
```

The REPL will automatically fall back to standard Python `input()` if `prompt-toolkit` is not available.

## Usage

### Start the REPL

```bash
# Using the adana command
adana

# Or using Python module
uv run python -m adana.apps.cli

# Or directly
uv run python -m adana.apps.repl
```

### Example Session

```python
>>> # Basic Python
>>> 2 + 2
4

>>> # Pre-imported classes (core)
>>> agent = BaseAgent()
>>> type(agent)
<class 'adana.core.agent.base_agent.BaseAgent'>

>>> # Pre-instantiated objects (ready to use!)
>>> research_agent.query(message="What is the OODA loop?")
>>> coordinator_agent.query(message="Coordinate the team to analyze this")
>>> todo_resource.query(message="List tasks")

>>> # Or create new instances
>>> my_researcher = ResearchAgent(agent_id="my-researcher")
>>> my_coordinator = CoordinatorAgent(agent_id="my-coordinator")
>>> my_workflow = ExampleWorkflow(workflow_id="my-workflow")
>>> my_todo = ToDoResource(resource_id="my-todo")

>>> # Multi-line input (ends with :)
>>> for i in range(3):
...     print(i)
...
0
1
2

>>> # Check available imports
>>> /imports
Pre-imported modules and classes:
  AnalysisAgent     (type)
  BaseAgent         (type)
  BaseResource      (type)
  BaseSTARAgent     (type)
  BaseWorkflow      (type)
  CoordinatorAgent  (type)
  ExampleWorkflow   (type)
  ResearchAgent     (type)
  STARAgent         (type)
  ToDoResource      (type)
  VerifierAgent     (type)
  logging           (module)

>>> # Get help
>>> /help

>>> # Exit
>>> /exit
```

## Commands

- `/help` - Show help and available commands
- `/imports` - List all pre-imported modules and classes
- `/exit` or `/quit` - Exit the REPL
- `Ctrl+D` - Exit the REPL
- `Ctrl+C` - Cancel current input

## Architecture

The REPL follows a simple 2-layer architecture:

```
CLI Router (adana/apps/cli/__main__.py)
    ↓
REPL Entry Point (adana/apps/repl/__main__.py)
    ↓
REPL Application (adana/apps/repl/repl_app.py)
```

### Components

- **CLI Router**: Routes between file execution and REPL mode
- **REPL Entry Point**: Simple entry point that instantiates the app
- **REPL Application**: Core REPL logic with prompt_toolkit integration

### Key Files

- `adana/apps/cli/__main__.py` - CLI router (~100 lines)
- `adana/apps/repl/__main__.py` - REPL entry point (~30 lines)
- `adana/apps/repl/repl_app.py` - REPL application (~250 lines)

## Customization

### Adding Pre-imports

Edit `adana/apps/repl/repl_app.py` in the `_setup_namespace()` method:

```python
def _setup_namespace(self) -> dict[str, Any]:
    namespace = {...}

    # Add your imports here
    from my_module import MyClass
    namespace["MyClass"] = MyClass

    return namespace
```

### Changing the Banner

Edit the `_show_welcome()` method in `repl_app.py`.

## Dependencies

**Optional (dev dependencies):**
- `prompt-toolkit>=3.0.0` - Interactive prompt with history and highlighting
- `pygments>=2.0.0` - Syntax highlighting for Python code

The REPL works without these dependencies but uses standard `input()` without enhanced features.

## Comparison with Dana REPL

| Feature | Dana REPL | Adana REPL |
|---------|-----------|------------|
| Architecture | 3-layer (Router/UI/Engine) | 2-layer (CLI/REPL) |
| Lines of code | ~1200 | ~380 |
| Syntax highlighting | ✓ | ✓ |
| Command history | ✓ | ✓ |
| Multi-line input | Auto-detect + `/` command | Auto-detect only |
| Progress indicators | ✓ | ✗ |
| ESC cancellation | ✓ | ✗ (Ctrl+C only) |
| Fullscreen mode | ✓ | ✗ |
| NLP mode | ✓ | ✗ |

The Adana REPL is intentionally simpler, focusing on core functionality while remaining easy to extend.