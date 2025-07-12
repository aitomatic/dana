# Unit Tests

This directory contains Python-based unit tests for individual Dana modules and components.

## Structure

- **`core/`** - Tests for `dana/core/` modules
  - Language features (syntax, semantics)
  - Runtime system
  - REPL functionality
  - Standard library
  - CLI tools

- **`agent/`** - Tests for `dana/agent/` modules
  - Agent system architecture
  - Agent capabilities
  - Resource management

- **`api/`** - Tests for `dana/api/` modules
  - Server implementation
  - Client implementation
  - API protocols

- **`frameworks/`** - Tests for `dana/frameworks/` modules
  - Knows framework
  - Poet framework
  - Agent frameworks

- **`integrations/`** - Tests for `dana/integrations/` modules
  - VSCode integration
  - MCP integration
  - Python integration
  - Agent-to-agent communication

- **`common/`** - Tests for `dana/common/` modules
  - Shared utilities
  - Configuration management
  - State management
  - Graph operations
  - I/O utilities
  - Mixins

- **`contrib/`** - Tests for `dana/contrib/` modules
  - Community contributions
  - Python-to-Dana utilities
  - RAG resources

## Running Unit Tests

```bash
# All unit tests
python -m pytest tests/unit/

# Specific module
python -m pytest tests/unit/core/
python -m pytest tests/unit/agent/

# With coverage
python -m pytest tests/unit/ --cov=dana
```

## Test Guidelines

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Speed**: Unit tests should be fast (< 100ms per test)
3. **Coverage**: Aim for high code coverage of the module being tested
4. **Mocking**: Use mocks for external dependencies
5. **Naming**: Use descriptive test names that explain what is being tested 