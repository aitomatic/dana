<div style="display: flex; align-items: center; gap: 10px;">
  <img src="../images/dana-logo.jpg" alt="Dana Logo" width="60">
  <span>
    <div style="font-size: 18px; font-style: italic; font-weight: 600; color: #666;">Agent-native programming language and runtime</div>
  </span>
</div>

# Dana — The Agent-Native Evolution of AI Development
*Beyond AI coding assistants: Write agents that learn, adapt, and improve themselves in production*

---
> **What if your agents could learn, adapt, and improve itself in production—without you?**

Welcome to the contributor guide for Dana! This is your comprehensive resource for understanding the architecture, extending capabilities, and contributing to the agent-native programming ecosystem.

# Dana for Contributors

Whether you're looking to contribute code, extend functionality, or deeply understand Dana's agent-native architecture that bridges AI coding assistance with autonomous systems, this guide provides everything you need to become an effective contributor to the Dana ecosystem.

---

## Quick Start for Contributors

### 1. Development Environment Setup
```bash
# Clone the repository
git clone https://github.com/aitomatic/opendxa.git
cd opendxa

# Set up development environment and run tests to verify setup
make dev
```

Note: Use `uv run` before commands or activate the venv: `source .venv/bin/activate`

### 2. Understand the Agent-Native Architecture and Codebase
Dana represents the convergence of development-time AI assistance and runtime autonomy through:
- Native `agent` primitives (not classes with AI bolted on)
- Context-aware execution that adapts `reason()` output types automatically  
- Self-improving pipeline composition with `|` operators
- POET-enabled adaptive functions that learn from production

- [Architecture Overview](architecture/README.md)
- [System Design](architecture/system-design.md)
- [Codebase](codebase/README.md)

### 3. Make Your First Contribution
- [Development Overview](development/README.md)
- [Contribution Guide](development/contribution-guide.md)

---

## Overview

Dana is built on an agent-native, modular, extensible architecture that represents the convergence of AI coding assistance and autonomous execution:

```
┌──────────────────────────────────────────────────────────┐
│                    Application Layer                     │
├──────────────────────────────────────────────────────────┤
│                      Agent Layer                         │
│ ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐ │
│ │    Agent    │ │ Capabilities │ │     Resources       │ │
│ │ Management  │ │    System    │ │    Management       │ │
│ └─────────────┘ └──────────────┘ └─────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│                   Dana Execution Layer                   │
│ ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐ │
│ │   Parser    │ │ Interpreter  │ │   Runtime Context   │ │
│ │    (AST)    │ │  (Executor)  │ │   (State Manager)   │ │
│ └─────────────┘ └──────────────┘ └─────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│                     Resource Layer                       │
│ ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐ │
│ │ LLM Resource│ │  Knowledge   │ │   External Tools    │ │
│ │Integration  │ │    Base      │ │     & Services      │ │
│ └─────────────┘ └──────────────┘ └─────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```


### Core Modules

#### `opendxa/dana/`
The heart of the Dana language implementation:
```
opendxa/
├── parser/ # Dana language parser and AST
├── interpreter/ # Dana program execution engine
├── sandbox/ # Execution context and state management
├── repl/ # Interactive development environment
└── transcoder/ # Natural language to Dana conversion
```

#### `opendxa/agent/`
Agent management and execution:
```
agent/
├── agent.py # Core Agent class and lifecycle
├── agent_runtime.py # Runtime execution environment
├── capability/ # Capability system implementation
└── resource/ # Resource management and integration
```

#### `opendxa/common/`
Shared utilities and base classes:
```
common/
├── config/ # Configuration management
├── resource/ # Base resource classes
├── utils/ # Utility functions and helpers
└── mixins/ # Reusable component mixins
```

### Key Files to Understand
1. `opendxa/dana/interpreter/interpreter.py` - Core Dana program execution logic
2. `opendxa/dana/parser/parser.py` - Dana language grammar and parsing
3. `opendxa/agent/agent.py` - Agent lifecycle and configuration
4. `opendxa/common/resource/llm_resource.py` - LLM integration and management

---

## Development Workflows

### Testing
```bash
# Run all tests
make test

# Run fast tests only (excludes live/deep tests)
make test-fast

# Run live tests (requires API keys)
make test-live

# Run tests and check coverage
make test-cov

# Run tests in watch mode (reruns on file changes)
make test-watch
```

### Code Quality
```bash
# Run linting checks
make lint

# Auto-fix linting issues
make lint-fix

# Format code with ruff
make format

# Run all code quality checks (lint + format-check + typecheck)
make check

# Auto-fix all fixable issues
make fix
```

---

## 🎨 Extension Development

### Creating Custom Capabilities

Capabilities extend agent functionality with reusable, composable modules:

```python
from opendxa.agent.capability.base_capability import BaseCapability

class CustomAnalysisCapability(BaseCapability):
    """Custom capability for specialized data analysis."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.analysis_model = self._load_model()

    def get_functions(self) -> dict:
        """Return Dana functions provided by this capability."""
        return {
            "analyze_data": self.analyze_data,
            "generate_insights": self.generate_insights,
        }

 def analyze_data(self, data, analysis_type="standard"):
 """Analyze data using custom algorithms."""
 # Implementation here
 return analysis_results

 def generate_insights(self, analysis_results):
 """Generate insights from analysis results."""
 # Implementation here
 return insights
```

### Creating Custom Resources

Resources provide external service integration:

```python
from opendxa.common.resource.base_resource import BaseResource

class CustomAPIResource(BaseResource):
    """Resource for integrating with custom API service."""

    def __init__(self, api_key: str, base_url: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._initialize_client()

 def get_functions(self) -> dict:
 """Return Dana functions for API operations."""
 return {
 "fetch_data": self.fetch_data,
 "submit_request": self.submit_request,
 }

 def fetch_data(self, endpoint: str, params: dict = None):
 """Fetch data from the API."""
 # Implementation here
 return api_response
```

### Dana Function Development
Add custom functions to the Dana language:

```python
from opendxa.dana.interpreter.function_registry import register_function

@register_function("custom_transform")
def custom_transform(data, transformation_type="default"):
    """Custom data transformation function for Dana."""
    if transformation_type == "normalize":
        return normalize_data(data)
    elif transformation_type == "aggregate":
        return aggregate_data(data)
    else:
        return apply_default_transform(data)
```

[Complete Extension Guide](extending/extension-development.md)

---

## 🧪 Testing and Quality Assurance

### Testing Strategy

Dana uses a comprehensive testing strategy to ensure reliability and quality:

```python
from opendxa.dana.interpreter import DanaInterpreter

# Unit tests for Dana functions
def test_custom_function():
    interpreter = DanaInterpreter()
    result = interpreter.eval("custom_transform([1, 2, 3])")
    assert result == [1, 2, 3]

# Integration tests for capabilities
def test_capability_integration():
    capability = CustomAnalysisCapability()
    functions = capability.get_functions()
    assert "analyze_data" in functions
```

### Quality Gates

1. **Code Coverage**: Minimum 80% coverage for new features
2. **Type Safety**: All Python code must pass mypy checks
3. **Documentation**: All public APIs must be documented
4. **Performance**: New features must not degrade performance by >5%

---

## 🤝 Contributing Process

### 1. Fork the Repository: Create your own fork of Dana

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes
- Follow the coding standards
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
make test
make lint
make typecheck
```

### 5. Submit a Pull Request
- Provide a clear description of changes
- Link any related issues
- Ensure all tests pass

---

## 📚 Learning Resources

### Architecture Deep Dives
- [System Design](architecture/system-design.md) - High-level architecture
- [Codebase Overview](codebase/README.md) - Code organization
- [Extension Development](extending/extension-development.md) - Building extensions

### Development Guides
- [Development Setup](development/README.md) - Environment setup
- [Contribution Guide](development/contribution-guide.md) - Contribution process

### Community and Support
- [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- [Discord Community](https://discord.gg/opendxa)

### Getting Started
- Look for issues labeled [good first issue](https://github.com/aitomatic/opendxa/labels/good%20first%20issue).*

---

*Ready to contribute? Start with the [Quick Start](#quick-start-for-contributors) or explore our [Extension Development Guide](extending/extension-development.md).*

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>