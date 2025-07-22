# Dana Workshop Integration Tests

This directory contains integration tests for all Dana examples in the `examples/workshop/` directory. These tests validate that workshop examples work correctly and demonstrate proper usage patterns.

## Overview

The workshop integration tests include:

- **Basic Language Features**: Tests for core Dana functionality like reasoning and type coercion
- **Resource Integration**: Tests for external resource usage (MCP, documents, web search)
- **Agent Examples**: Tests for individual agents and agent structures
- **System of Agents**: Tests for multi-agent workflows and coordination
- **Python Interoperability**: Tests for Dana-Python integration patterns
- **Syntax Validation**: Comprehensive syntax checking for all `.na` files

## Test Files

- `test_workshop_examples.py` - Main integration test suite
- `run_workshop_tests.py` - Test runner script with environment setup
- `workshop_tests_README.md` - This documentation file

## Running Tests

### Prerequisites

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Ensure Dana is installed:
   ```bash
   cd /path/to/opendxa
   make install
   ```

### Basic Usage

```bash
# Run all workshop tests (mock mode)
python tests/integration/run_workshop_tests.py

# Run with verbose output
python tests/integration/run_workshop_tests.py -v

# Run specific tests by keyword
python tests/integration/run_workshop_tests.py -k builtin

# Run only file validation
python tests/integration/run_workshop_tests.py --file-validation

# Run only parametrized tests
python tests/integration/run_workshop_tests.py --parametrized

# Run with MCP server (installs and starts weather MCP server)
python tests/integration/run_workshop_tests.py --with-mcp
```

### Alternative: Direct pytest Usage

```bash
# From project root
cd /path/to/opendxa

# Run all workshop tests
python -m pytest tests/integration/test_workshop_examples.py -v

# Run specific test method
python -m pytest tests/integration/test_workshop_examples.py::TestWorkshopExamples::test_basic_language_features -v

# Run parametrized tests only
python -m pytest tests/integration/test_workshop_examples.py -k "test_workshop_file_execution" -v
```

## Test Categories

### 1. Basic Language Features
Tests core Dana language functionality:
- Built-in reasoning (`builtin_reasoning.na`)
- Semantic type coercion (`semantic_type_coercion.na`)

### 2. Resource Integration
Tests external resource usage (may require mock mode):
- Document querying (`docs_resource.na`)
- MCP server integration (`mcp_resource.na`)
- Web search capabilities

### 3. Agent Examples
Tests individual agent implementations:
- Reasoning agents (`reasoning_using_an_agent.na`)
- Agent structure validation
- Function definition requirements

### 4. System of Agents
Tests multi-agent coordination:
- General management agent (`gma.na`)
- Specialist agents (`specialist_agent_*.na`)
- Agent pool management

### 5. Python Interoperability
Tests Dana-Python integration:
- Order intelligence example (`order_intelligence.na`)
- Function definitions for Python calling

### 6. Syntax Validation
Comprehensive syntax checking for all workshop `.na` files:
- Parse validation without execution
- Error reporting for syntax issues
- File discovery and validation

## Test Modes

### Mock Mode (Default)
The tests run in mock mode by default (`DANA_MOCK_LLM=true`), which means:

- LLM API calls are mocked and don't require real API keys
- External services (MCP servers, web search) may not be available
- Some tests may fail due to missing external dependencies (this is expected)
- Focus is on syntax validation and basic execution paths

### MCP Integration Mode
Use `--with-mcp` flag to enable full MCP server integration:

- Automatically installs the MCP weather server package
- Starts the MCP server in the background during tests
- Disables mock mode for realistic MCP resource testing
- Stops the MCP server when tests complete
- Requires internet connection for installation

**MCP Server Details:**
- Package: `IsDaniel.MCP-Weather-Server` from GitHub
- Protocol: `streamable-http` (runs on port 8000 by default)
- Used by: `mcp_resource.na`, `reasoning_using_an_agent.na`

## Expected Behavior

### Tests That Should Pass
- Syntax validation for all `.na` files
- Basic language features in mock mode
- File existence checks
- Agent structure validation
- Python interoperability examples

### Tests That May Fail (Expected in Mock Mode)
- Resource examples requiring external services
- MCP server integrations without running servers
- Web search functionality without internet access
- Agent examples with external dependencies

### Tests That Should Pass with `--with-mcp`
- MCP resource integration (`mcp_resource.na`)
- MCP-based reasoning agents (`reasoning_using_an_agent.na`)
- Weather-related functionality through MCP server

## Test Structure

The tests follow the table-driven test approach using pytest parametrize:

```python
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "builtin_reasoning",
            "file_path": "1_dana_language_and_runtime/builtin_reasoning.na",
            "should_succeed": True,
            "description": "Basic reasoning functionality"
        },
        # ... more test cases
    ],
    ids=lambda x: x["name"]
)
def test_workshop_file_execution(test_case):
    # Test implementation
```

## Adding New Tests

To add tests for new workshop examples:

1. Add the file path to the `expected_files` list in `test_workshop_file_existence()`
2. Add a new test case to the parametrized `test_workshop_file_execution()` function
3. Set `should_succeed` based on whether the example requires external dependencies

## Integration with CI/CD

These tests can be integrated into continuous integration pipelines:

```yaml
# Example GitHub Actions step
- name: Run workshop integration tests
  run: |
    source .venv/bin/activate
    python tests/integration/run_workshop_tests.py --syntax-only
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and Dana is installed
2. **Missing Files**: Workshop examples may be added/removed - update test expectations
3. **External Dependencies**: Many examples require external services - use `--with-mcp` or mock mode
4. **Path Issues**: Tests assume they're run from the project root directory
5. **MCP Installation Failures**: 
   - Ensure internet connection for GitHub package download
   - Check pip/Python permissions for package installation
   - Verify virtual environment is properly activated
6. **MCP Server Port Conflicts**: 
   - Default port 8000 may be in use by other services
   - Stop other services or kill existing processes on port 8000

### Debug Mode

For detailed debugging information:

```bash
# Enable debug logging
DANA_DEBUG=1 python tests/integration/run_workshop_tests.py -v

# Run individual test with full output
python -m pytest tests/integration/test_workshop_examples.py::TestWorkshopExamples::test_basic_language_features -v -s
```

## Contributing

When adding new workshop examples:

1. Ensure the example has proper Dana syntax
2. Add appropriate test cases to the integration test suite
3. Update documentation with any new requirements
4. Test both success and failure scenarios

---

For more information about the Dana workshop examples, see `examples/workshop/README.md`. 