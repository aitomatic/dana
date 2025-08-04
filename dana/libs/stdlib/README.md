# Dana Standard Library Design

## Overview

Dana's standard library follows a **core vs non-core** design pattern that balances convenience with explicit control:

- **Core stdlib**: Automatically available in all Dana programs
- **Non-core stdlib**: Requires explicit import statements

## Design Philosophy

### Core Stdlib (Automatically Available)
- **Essential functionality** that every Dana program needs
- **Zero import friction** - always available
- **High security** - trusted functions with sandbox access
- **Performance optimized** - loaded once at interpreter startup

### Non-Core Stdlib (Explicit Import)
- **Advanced utilities** and specialized functionality
- **Explicit control** - developers choose what to import
- **Modular design** - only load what you need
- **Extensible** - easy to add new modules

## Current Structure

```
dana/core/stdlib/
├── core/                    # Automatically available
│   ├── agent_function.py    # Core agent creation
│   ├── llm_function.py      # Core LLM functionality
│   ├── log_function.py      # Core logging
│   ├── print_function.py    # Core output
│   ├── reason_function.py   # Core reasoning
│   └── register_core_functions.py  # Auto-registration
├── pythonic/                # Pythonic built-ins (auto-loaded)
│   └── function_factory.py  # Python function wrappers
└── agent/                   # Non-core agent utilities
    ├── __init__.py
    ├── agent_utils.py       # Agent utilities
    └── agent_templates.py   # Agent templates
```

## Agent Stdlib Implementation

### Core Agent Functionality (Auto-Available)

The `agent()` function is automatically available in all Dana programs:

```dana
# No import required - always available
inspector = agent("QualityInspector", {
    "domain": "semiconductor",
    "tolerance_threshold": 0.015
})

# Built-in methods always available
plan = inspector.plan("Inspect wafer batch")
solution = inspector.solve("High defect rate issue")
inspector.remember("key", "value")
data = inspector.recall("key")
```

**Core agent capabilities:**
- ✅ `agent()` function - create agents with AI capabilities
- ✅ Built-in methods: `plan()`, `solve()`, `remember()`, `recall()`, `chat()`
- ✅ Memory system with conversation history
- ✅ LLM integration for AI-powered responses
- ✅ Type safety and struct system integration

### Non-Core Agent Functionality (Explicit Import)

Advanced agent utilities require explicit imports:

```dana
# Explicit import required
import agent

# Advanced utilities
agents = create_agent_pool("CustomerService", 3, configs)
cs_agent = agent_from_template("customer_service", domain="billing")
metrics = agent_metrics(my_agent)
results = agent_benchmark(my_agent, tasks)
```

**Non-core agent capabilities:**
- 📦 Agent pools for parallel processing
- 📦 Pre-built templates for common use cases
- 📦 Configuration management (load/save)
- 📦 Performance benchmarking and metrics
- 📦 Advanced agent utilities

## Registration Mechanism

### Core Functions
Core functions are automatically registered in `DanaInterpreter._init_function_registry()`:

```python
def _init_function_registry(self):
    # Register all core functions automatically
    register_core_functions(self._function_registry)
```

The `register_core_functions()` function:
1. Scans `dana/core/stdlib/core/` directory
2. Finds all functions ending with `_function`
3. Registers them with `trusted_for_context=True`
4. Gives them highest priority in function resolution

### Non-Core Modules
Non-core modules use Dana's import system:

```dana
# Explicit import loads the module
import agent

# Functions become available in current scope
agents = create_agent_pool("MyAgent", 5)
```

## Security Model

### Core Functions
- **Trusted by default** - `trusted_for_context=True`
- **Sandbox access** - can access context and resources
- **High priority** - override built-in functions
- **Carefully curated** - only essential functionality

### Non-Core Functions
- **Standard security** - follow normal sandbox rules
- **Explicit permission** - developers choose what to import
- **Modular isolation** - separate security contexts
- **Extensible** - can add new security models

## Usage Patterns

### Simple Agent Usage (Core Only)
```dana
# Just use the agent keyword - no imports needed
agent QualityInspector:
    domain: str = "semiconductor"
    tolerance: float = 0.015

inspector = QualityInspector()
plan = inspector.plan("Inspect production line")
```

### Advanced Agent Usage (Core + Non-Core)
```dana
# Core functionality
agent QualityInspector:
    domain: str = "semiconductor"

inspector = QualityInspector()

# Non-core utilities
import agent

# Create agent team
team = create_agent_pool("QualityInspector", 5, configs)

# Use templates
cs_agent = agent_from_template("customer_service")

# Get metrics
metrics = agent_metrics(inspector)
```

## Benefits of This Design

### For Developers
- **Low friction** - core functionality always available
- **Explicit control** - choose advanced features when needed
- **Clear boundaries** - understand what's core vs optional
- **Performance** - only load what you use

### For the Language
- **Consistent experience** - core functions always work
- **Extensible** - easy to add new stdlib modules
- **Secure** - clear security boundaries
- **Maintainable** - modular organization

### For the Ecosystem
- **Standard patterns** - consistent across all stdlib modules
- **Community contributions** - easy to add non-core modules
- **Backward compatibility** - core functions never change
- **Forward compatibility** - new core functions added carefully

## Future Extensions

This pattern can be extended to other stdlib areas:

- **Math stdlib**: Core math functions auto-available, advanced math requires import
- **Data stdlib**: Core data structures auto-available, advanced analytics requires import
- **Web stdlib**: Core HTTP functions auto-available, advanced web features require import
- **ML stdlib**: Core ML functions auto-available, advanced ML requires import

Each follows the same pattern: core functionality for common use cases, non-core for advanced features. 