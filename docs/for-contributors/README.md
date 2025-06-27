# OpenDXA for Contributors

Whether you're looking to contribute code, extend functionality, or deeply understand OpenDXA's agent-native architecture, this guide provides everything you need to become an effective contributor to the OpenDXA ecosystem.

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
- [Architecture Overview](architecture/README.md)
- [System Design](architecture/system-design.md)
- [Codebase](codebase/README.md)

### 3. Make Your First Contribution
- [Development Overview](development/README.md)
- [Contribution Guide](development/contribution-guide.md)

---

## Overview

OpenDXA is built on an agent-native, modular, extensible architecture with clear separation of concerns:

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
dana/
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
- Unit Tests: Test individual components in isolation
- Integration Tests: Test component interactions
- End-to-End Tests: Test complete user workflows
- Performance Tests: Validate performance characteristics
- Regression Tests: Prevent breaking changes

### Test Structure
```
tests/
├── unit/ # Unit tests for individual components
│ ├── dana/ # Dana language tests
│ ├── agent/ # Agent system tests
│ └── common/ # Common utilities tests
├── integration/ # Integration tests
├── e2e/ # End-to-end tests
├── performance/ # Performance and load tests
└── fixtures/ # Test data and fixtures
```

### Writing Tests
```python
import pytest
from opendxa.dana.interpreter import DanaInterpreter

class TestDanaInterpreter:
 """Test suite for Dana interpreter functionality."""

 def test_basic_assignment(self):
 """Test basic variable assignment."""
 interpreter = DanaInterpreter()
 result = interpreter.execute("x = 42")
 assert result.success
 assert interpreter.context.get("x") == 42

 def test_function_call(self):
 """Test function call execution."""
 interpreter = DanaInterpreter()
 result = interpreter.execute('result = reason("test prompt")')
 assert result.success
 assert "result" in interpreter.context
```

---

## 🤝 Community and Contribution

### Contribution Process
1. Fork the Repository: Create your own fork of OpenDXA
2. Create Feature Branch: Work on a dedicated branch for your changes
3. Make Changes: Implement your feature or fix
4. Write Tests: Ensure your changes are well-tested
5. Update Documentation: Document new features or changes
6. Submit Pull Request: Create a PR with clear description
7. Code Review: Collaborate with maintainers on feedback
8. Merge: Once approved, your changes are merged

### Code Review Guidelines
- Clear Description: Explain what your changes do and why
- Small, Focused PRs: Keep changes focused and reviewable
- Test Coverage: Include tests for new functionality
- Documentation: Update docs for user-facing changes
- Backward Compatibility: Avoid breaking existing functionality

---

## Roadmap and Future Development

### Current Focus Areas
- Performance Optimization: Improving execution speed and memory usage
- Language Features: Expanding Dana language capabilities
- Integration Ecosystem: More resource providers and capabilities
- Developer Experience: Better tooling and debugging support

### Upcoming Features
- Visual Debugging: Graphical debugging and state inspection
- Distributed Execution: Multi-node agent execution
- Advanced Analytics: Built-in performance and behavior analytics
- IDE Integration: Enhanced support for popular development environments

---

## 📞 Getting Help

- [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- [Discord Community](https://discord.gg/opendxa)

---

*Ready to contribute? Start with our [Development Guide](development/README.md) or check out [Good First Issues](https://github.com/aitomatic/opendxa/labels/good%20first%20issue).*

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>