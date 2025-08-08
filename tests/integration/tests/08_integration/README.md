# Phase 8: Integration Tests

This directory contains comprehensive tests for Dana's integration capabilities, covering MCP integration, Python interoperability, and agent system functionality.

## Overview

Phase 8 tests ensure that Dana's integration features work correctly with external systems and maintain compatibility across different environments. These tests validate:

1. **MCP Integration** - Model Context Protocol server and client interactions
2. **Python Interoperability** - Bidirectional integration between Dana and Python
3. **Agent System** - Agent struct definitions, methods, and communication

## Test Categories

### 8.1 MCP Integration (4 tests)
- `test_mcp_basic.na` - Basic MCP server integration and connectivity
- `test_mcp_tools.na` - MCP tool usage and execution
- `test_mcp_resources.na` - MCP resource management and lifecycle
- `test_mcp_error_handling.na` - MCP error scenarios and recovery

### 8.2 Python Interoperability (4 tests)
- `test_python_import.na` - Importing Python modules into Dana
- `test_python_functions.na` - Calling Python functions from Dana
- `test_python_objects.na` - Python object interaction and manipulation
- `test_python_types.na` - Python type compatibility and conversions

### 8.3 Agent System (5 tests)
- `test_agent_definition.na` - Agent struct definitions and instantiation
- `test_agent_methods.na` - Built-in agent methods (plan, solve, remember, recall)
- `test_agent_memory.na` - Agent memory operations and persistence
- `test_agent_communication.na` - Agent-to-agent communication
- `test_agent_pools.na` - Agent pool management and lifecycle

## Test Structure

Each test file follows the standard Dana test structure:

```na
# Test: [Test Name]
# Purpose: [Brief description of what is being tested]
# Category: Integration - [Subcategory]

log("Starting [Test Name] test")

# Test setup
# ... setup code ...

# Test cases with assertions
# ... test cases ...

log("[Test Name] test completed successfully")
```

## Prerequisites

### For MCP Tests
- MCP test server running (examples/05_mcp_integration/start_sse_server.py)
- Port 8080 available for SSE server
- Network connectivity for MCP operations

### For Python Tests
- Python environment with required packages
- Dana Python integration modules available
- Compatible Python version (3.8+)

### For Agent Tests
- Dana agent system enabled
- Sufficient memory for agent operations
- LLM resources configured (for agent reasoning)

## Running Tests

### Individual Tests
```bash
# Activate Dana environment
source .venv/bin/activate

# Run specific test categories
dana tests/integration/tests/08_integration/test_mcp_basic.na
dana tests/integration/tests/08_integration/test_python_import.na
dana tests/integration/tests/08_integration/test_agent_definition.na
```

### All Phase 8 Tests
```bash
# Run all integration tests
python tests/integration/tests/08_integration/run_phase8_tests.py
```

### Test Dependencies
```bash
# Start MCP test server (separate terminal)
cd examples/05_mcp_integration
python start_sse_server.py

# Ensure Python environment is set up
pip install -r requirements.txt
```

## Expected Results

### Success Criteria
- All tests pass without errors
- Integration points work correctly
- Error handling behaves as expected
- Performance is within acceptable limits

### Test Coverage
- **MCP Integration**: 25+ test cases covering connectivity, tools, resources, and error handling
- **Python Interoperability**: 30+ test cases covering imports, functions, objects, and type compatibility
- **Agent System**: 40+ test cases covering definitions, methods, memory, communication, and pools

### Performance Benchmarks
- MCP operations: < 5 seconds per test
- Python interop: < 2 seconds per test
- Agent operations: < 10 seconds per test (due to LLM calls)

## Known Limitations

### MCP Integration
- Requires external MCP server for full testing
- Network-dependent operations may be flaky
- Some MCP features may not be available in test environment

### Python Interoperability
- Python version compatibility varies
- Some Python packages may not be available in Dana sandbox
- Type conversion edge cases may exist

### Agent System
- Agent features require LLM resources
- Memory operations may be limited in test environment
- Agent-to-agent communication requires multiple agent instances

## Troubleshooting

### Common Issues

**MCP Connection Failures**
```
Error: Failed to connect to MCP server
Solution: Ensure MCP test server is running on port 8080
```

**Python Import Errors**
```
Error: Module not found
Solution: Verify Python environment and Dana Python integration setup
```

**Agent Method Errors**
```
Error: Agent method not available
Solution: Ensure agent system is properly initialized and LLM resources are available
```

### Debug Mode
Enable detailed logging for troubleshooting:
```na
# Add at the beginning of test files
debug_mode = true
log_level = "debug"
```

## Maintenance

### Regular Updates
- Update MCP server configurations as needed
- Sync with Python integration changes
- Refresh agent system capabilities as they evolve

### Performance Monitoring
- Track test execution times
- Monitor resource usage during tests
- Identify and optimize slow tests

### Documentation
- Keep test cases documented with clear purposes
- Update prerequisites as dependencies change
- Maintain troubleshooting guide

## Test Implementation Status

### Phase 8 Progress: 13/13 tests implemented (100%) ✅ COMPLETED

#### 8.1 MCP Integration - 4/4 (100%) ✅
- [x] `test_mcp_basic.na` - Basic MCP server integration (10 test cases)
- [x] `test_mcp_tools.na` - MCP tool usage (12 test cases)
- [x] `test_mcp_resources.na` - MCP resource management (12 test cases)
- [x] `test_mcp_error_handling.na` - MCP error scenarios (12 test cases)

#### 8.2 Python Interoperability - 4/4 (100%) ✅
- [x] `test_python_import.na` - Importing Python modules (13 test cases)
- [x] `test_python_functions.na` - Calling Python functions (12 test cases)
- [x] `test_python_objects.na` - Python object interaction (12 test cases)
- [x] `test_python_types.na` - Python type compatibility (10 test cases)

#### 8.3 Agent System - 5/5 (100%) ✅
- [x] `test_agent_definition.na` - Agent struct definitions (10 test cases)
- [x] `test_agent_methods.na` - Built-in agent methods (10 test cases)
- [x] `test_agent_memory.na` - Agent memory operations (10 test cases)
- [x] `test_agent_communication.na` - Agent-to-agent communication (10 test cases)
- [x] `test_agent_pools.na` - Agent pool management (10 test cases)

### Implementation Summary
- **Total Test Cases**: 133+ individual test cases across all integration categories
- **Automated Test Runner**: `run_phase8_tests.py` with comprehensive reporting
- **Documentation**: Complete README with setup instructions and troubleshooting
- **Coverage**: 100% of planned Phase 8 integration functionality
- **Quality**: All tests include error handling, edge cases, and performance considerations

This comprehensive test suite will ensure Dana's integration capabilities are robust, reliable, and maintain compatibility across different environments and use cases.
