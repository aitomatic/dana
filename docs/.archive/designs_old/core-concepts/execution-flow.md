<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# Execution Flow in OpenDXA

## Overview

The execution flow in OpenDXA defines how agents process tasks using the Dana language. Dana (Domain-Aware NeuroSymbolic Architecture) provides an imperative programming model that combines domain expertise with LLM-powered reasoning to achieve complex objectives.

## Core Concepts

### 1. Execution Components

- **Dana Language**
  - Imperative programming language
  - Domain-specific syntax
  - State-based operations
  - Built-in reasoning functions

- **Dana Interpreter**
  - AST-based execution
  - State management
  - Function registry
  - Error handling

- **Runtime Context**
  - [State management](./state-management.md)
  - Resource access
  - Progress tracking
  - Error handling

### 2. Execution Operations

- Dana program execution
- [State management](./state-management.md)
- Resource coordination
- Error handling
- Progress monitoring

## Execution Flow

The typical execution flow in OpenDXA follows these steps:

1. **Request Interpretation**: Incoming user requests are analyzed and converted to execution objectives
2. **Program Generation**: Dana programs are generated either directly or via the transcoder
3. **Context Initialization**: Runtime context with appropriate state containers is created
4. **Program Execution**: The Dana interpreter executes the program statements
5. **Response Generation**: Results are assembled and returned to the user

## Implementation

### 1. Dana Program Execution

```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Define a Dana program
dana_program = """
# Initialize variables
temp.data = world.input_data
temp.processed = []

# Process data
for item in temp.data:
    temp.result = reason("Analyze this item: {item}")
    temp.processed.append(temp.result)

# Generate summary
agent.summary = reason("Summarize the following analysis: {temp.processed}")
log.info("Analysis complete with summary: {agent.summary}")
"""

# Create context and run program
context = SandboxContext(
    agent={},
    world={"input_data": ["item1", "item2", "item3"]},
    temp={}
)
result = run(dana_program, context)
```

### 2. State Management

```python
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Initialize context with state
context = SandboxContext()

# Set state values
context.set("agent.name", "analyst_agent") 
context.set("world.data_source", "customer_feedback.csv")
context.set("temp.processing_started", True)

# Get state values
agent_name = context.get("agent.name")
data_source = context.get("world.data_source")
```

*See [State Management](./state-management.md) for comprehensive details.*

### 3. Error Handling

```python
try:
    result = run(dana_program, context)
except Exception as e:
    # Log error
    print(f"Execution failed: {e}")
    
    # Update state
    context.set("agent.status", "error")
    context.set("agent.error", str(e))
    
    # Handle error based on type
    if "NameError" in str(e):
        # Handle variable resolution error
        pass
    elif "TypeError" in str(e):
        # Handle type error
        pass
```

## Key Differentiators

1. **Imperative Programming Model**
   - Clear, sequential program flow
   - Explicit state management
   - Direct conditional logic
   - First-class function support

2. **Integrated Reasoning**
   - `reason()` function for LLM-powered reasoning
   - Seamless integration of symbolic and neural processing
   - Context-aware reasoning with f-string templates
   - Stateful reasoning across operations

3. **Runtime Flexibility**
   - Dynamic state creation and access
   - Resource integration and coordination
   - Error recovery and handling
   - Progress tracking and monitoring

## Best Practices

1. **Program Design**
   - Clear, modular Dana programs
   - Proper state scoping and organization
   - Error handling and validation
   - State management *(See [State Management](./state-management.md))*

2. **Execution Control**
   - Resource management
   - Progress tracking
   - Error recovery
   - Performance monitoring

3. **State Management**
   - Clear state structure
   - Proper access patterns
   - State persistence
   - Context maintenance

## Common Patterns

1. **Sequential Processing**
   ```python
   # Dana program for sequential processing
   dana_program = """
   # Initialize state
   temp.data = world.input
   
   # Process sequentially
   temp.step1 = reason("Process step 1: {temp.data}")
   temp.step2 = reason("Process step 2 with previous result: {temp.step1}")
   temp.step3 = reason("Process step 3 with previous result: {temp.step2}")
   
   # Store final result
   agent.result = temp.step3
   """
   ```

2. **Conditional Processing**
   ```python
   # Dana program with conditional logic
   dana_program = """
   # Check conditions
   temp.sentiment = reason("Analyze sentiment in: {world.text}")
   
   # Conditional processing
   if "positive" in temp.sentiment:
       agent.response = reason("Generate positive response to: {world.text}")
   elif "negative" in temp.sentiment:
       agent.response = reason("Generate empathetic response to: {world.text}")
   else:
       agent.response = reason("Generate neutral response to: {world.text}")
   
   # Log result
   log.info("Generated response: {agent.response}")
   """
   ```

3. **Iterative Processing**
   ```python
   # Dana program with iteration
   dana_program = """
   # Initialize
   temp.items = world.data_items
   temp.results = []
   
   # Process each item
   for item in temp.items:
       temp.analysis = reason("Analyze this item: {item}")
       temp.results.append(temp.analysis)
   
   # Summarize results
   agent.summary = reason("Summarize these analyses: {temp.results}")
   """
   ```

## Execution Examples

1. **Data Analysis**
   - Data loading and preparation
   - Feature extraction and transformation
   - Analysis execution
   - Result generation

2. **Process Automation**
   - Task decomposition
   - Resource allocation
   - Execution control
   - Error handling

3. **Conversational Assistance**
   - Context analysis
   - Knowledge retrieval
   - Response generation
   - Memory management

## Next Steps

- Learn about [Agents](./agent.md)
- Understand [Dana Language](../dana/language.md)
- Understand [State Management](./state-management.md)
- Explore [Resources](./resources.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>