# Resource System Tests

This directory contains comprehensive tests for Dana's resource system, covering the `resource` keyword functionality and its integration with other Dana features.

## Test Files

### `test_resource_basic.na`
Basic resource functionality tests:
- Resource definition and instantiation
- Field access and default values
- Different field types (str, int, float, bool, list, dict)
- Resource inheritance from BaseResource
- Resource methods using struct-function pattern
- Resource lifecycle (start/stop)
- Standard query interface
- Resource definitions with comments

### `test_resource_advanced.na`
Advanced resource scenarios:
- Resource composition (multiple resources working together)
- Multi-level inheritance chains
- Error handling and exception management
- State management and transitions
- Complex default values
- Method overloading patterns
- Context manager behavior

### `test_resource_integration.na`
Integration tests with other Dana features:
- Resource usage with agents and agent blueprints
- Resource methods within agent contexts
- Resource integration with workflows
- Concurrency and resource safety
- Promise system integration
- Struct system integration
- Function system integration

### `test_resource_edge_cases.na`
Edge cases and error scenarios:
- Empty resource definitions
- Duplicate field name handling
- Circular reference management
- Memory management and cleanup
- Concurrent access patterns
- Error recovery and resilience
- Boundary conditions
- Type safety validation
- Performance limits

## Running the Tests

To run all resource tests:

```bash
# Run basic tests
dana tests/unit/core/resource/test_resource_basic.na

# Run advanced tests
dana tests/unit/core/resource/test_resource_advanced.na

# Run integration tests
dana tests/unit/core/resource/test_resource_integration.na

# Run edge case tests
dana tests/unit/core/resource/test_resource_edge_cases.na
```

## Test Coverage

The test suite covers:

### Core Functionality
- ✅ Resource definition syntax
- ✅ Resource instantiation
- ✅ Field access and modification
- ✅ Default value handling
- ✅ Type preservation
- ✅ Inheritance from BaseResource

### Methods and Behavior
- ✅ Struct-function pattern for methods
- ✅ Method parameter handling
- ✅ Return value processing
- ✅ Method overloading
- ✅ Context manager support

### Integration Features
- ✅ Agent blueprint compatibility
- ✅ Workflow integration
- ✅ Concurrency safety
- ✅ Promise system support
- ✅ Struct system integration
- ✅ Function system integration

### Error Handling
- ✅ Exception propagation
- ✅ Error recovery mechanisms
- ✅ Boundary condition handling
- ✅ Type safety validation
- ✅ Memory management

### Edge Cases
- ✅ Empty definitions
- ✅ Duplicate field handling
- ✅ Circular reference management
- ✅ Performance constraints
- ✅ Concurrent access patterns

## Resource System Features Tested

Based on the documentation in `docs/primers/resource.md`, these tests verify:

1. **Resource Definition**: The `resource` keyword for defining resource types
2. **Resource Instantiation**: Creating resource instances with custom field values
3. **Struct-Function Pattern**: Defining resource behavior through external functions
4. **Standard Query Interface**: The `query(request: str) -> str` method pattern
5. **Resource Lifecycle**: start/stop/suspend/resume methods
6. **Resource Inheritance**: Extending BaseResource and creating inheritance chains
7. **Resource Composition**: Combining multiple resources for complex workflows
8. **Agent Integration**: Resource usage within agent contexts (current implementation)
9. **Error Handling**: Proper error propagation and recovery
10. **Type Safety**: Field type validation and preservation

## Expected Behavior

The tests verify that the resource system:

- Allows defining resources as specialized structs
- Supports field definitions with types and default values
- Enables method definition through the struct-function pattern
- Provides proper inheritance from BaseResource
- Maintains type safety throughout
- Handles errors gracefully
- Integrates well with other Dana features
- Supports complex resource compositions
- Manages resource lifecycles properly

## Notes

- These tests focus on the current implementation status as described in the documentation
- The agent `.use()` method integration is noted as a future enhancement
- Tests are designed to be comprehensive while remaining practical and maintainable
- All tests include detailed assertions and error messages for debugging
- Tests follow Dana's testing patterns and conventions
