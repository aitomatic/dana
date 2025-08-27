# Workflow System Tests

This directory contains comprehensive tests for Dana's workflow system, covering the `workflow` keyword functionality and its integration with other Dana features.

## Test Files

### `test_workflow_basic.na`
Basic workflow functionality tests:
- Workflow definition and instantiation
- Default field access (name, fsm)
- Field access and custom values
- Different field types (str, int, float, bool, list, dict)
- Workflow inheritance
- Workflow methods using struct-function pattern
- Workflow execution state tracking
- Workflow definitions with comments

### `test_workflow_advanced.na`
Advanced workflow scenarios:
- Workflow composition (multiple workflows working together)
- Multi-level inheritance chains
- Error handling and exception management
- State management and transitions
- Complex default values
- Method overloading patterns
- FSM integration

### `test_workflow_integration.na`
Integration tests with other Dana features:
- Workflow usage with agents and agent blueprints
- Workflow methods within agent contexts
- Workflow integration with resources
- Concurrency and workflow safety
- Promise system integration
- Struct system integration
- Function system integration

### `test_workflow_edge_cases.na`
Edge cases and error scenarios:
- Empty workflow definitions
- Duplicate field name handling
- Circular reference management
- Memory management and cleanup
- Concurrent access patterns
- Error recovery and resilience
- Boundary conditions
- Type safety validation
- Performance limits

## Running the Tests

To run all workflow tests:

```bash
# Run basic tests
dana tests/unit/core/workflow/test_workflow_basic.na

# Run advanced tests
dana tests/unit/core/workflow/test_workflow_advanced.na

# Run integration tests
dana tests/unit/core/workflow/test_workflow_integration.na

# Run edge case tests
dana tests/unit/core/workflow/test_workflow_edge_cases.na
```

## Test Coverage

The test suite covers:

### Core Functionality
- ✅ Workflow definition syntax
- ✅ Workflow instantiation
- ✅ Default field access (name, fsm)
- ✅ Field access and modification
- ✅ Default value handling
- ✅ Type preservation
- ✅ Inheritance

### Methods and Behavior
- ✅ Struct-function pattern for methods
- ✅ Method parameter handling
- ✅ Return value processing
- ✅ Method overloading
- ✅ Execution state tracking

### Integration Features
- ✅ Agent blueprint compatibility
- ✅ Resource integration
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

## Workflow System Features Tested

Based on the workflow implementation, these tests verify:

1. **Workflow Definition**: The `workflow` keyword for defining workflow types
2. **Default Fields**: Automatic inclusion of `name: str = "A Workflow"` and `fsm: FSM = None`
3. **Workflow Instantiation**: Creating workflow instances with custom field values
4. **Struct-Function Pattern**: Defining workflow behavior through external functions
5. **Execution State Tracking**: Built-in state management and history tracking
6. **Workflow Inheritance**: Extending base workflows and creating inheritance chains
7. **Workflow Composition**: Combining multiple workflows for complex processes
8. **Agent Integration**: Workflow usage within agent contexts
9. **Error Handling**: Proper error propagation and recovery
10. **Type Safety**: Field type validation and preservation

## Expected Behavior

The tests verify that the workflow system:

- Allows defining workflows as specialized structs
- Automatically includes default fields (name, fsm)
- Supports field definitions with types and default values
- Enables method definition through the struct-function pattern
- Provides execution state tracking and history
- Integrates seamlessly with Dana's type system
- Works with agents, resources, and other Dana features
- Maintains proper error handling and recovery
- Supports inheritance and composition patterns
- Provides lifecycle management through the registry system

## Registry Integration

Workflows are fully integrated with Dana's registry system:

- **Type Registration**: Workflow types are registered in TYPE_REGISTRY
- **Instance Tracking**: Workflow instances are tracked in WORKFLOW_REGISTRY
- **Global Registry**: Workflows are accessible through GLOBAL_REGISTRY
- **Statistics**: Workflow types and instances are included in registry statistics
- **Cleanup**: Workflows are properly cleaned up during registry clear operations
