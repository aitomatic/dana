# DANA Interpreter Architecture

## Component Diagram

```
┌─────────────────────────────┐
│                             │
│       Interpreter           │
│                             │
└───────────────┬─────────────┘
                │
                │ delegates
                ▼
┌─────────────────────────────┐
│                             │
│    StatementExecutor        │
│                             │
└───┬───────────┬─────────────┘
    │           │
    │           │ uses
    │           ▼
    │   ┌─────────────────────┐
    │   │                     │
    │   │ ExpressionEvaluator │
    │   │                     │
    │   └─────────────────────┘
    │
    │ uses
    ▼
┌─────────────────────────────┐     ┌─────────────────────────┐
│                             │     │                         │
│       LLMIntegration        │     │    ContextManager       │
│                             │     │                         │
└─────────────────────────────┘     └─────────────────────────┘
```

## Class Responsibilities

### Interpreter
- Maintains the API for backward compatibility
- Orchestrates the execution flow
- Manages program-level hooks
- Delegates actual execution to specialized components

### StatementExecutor
- Executes different types of statements
- Handles statement-specific logic
- Delegates expression evaluation to ExpressionEvaluator
- Manages control flow for conditionals and loops

### ExpressionEvaluator
- Evaluates expressions (binary, literal, identifier)
- Resolves variable references
- Handles f-string interpolation
- Returns computed values for use in statements

### LLMIntegration
- Handles interactions with Large Language Models
- Processes reason statements
- Manages context preparation for LLM calls
- Formats and processes LLM responses

### ContextManager
- Manages variable scopes and resolution
- Provides access to the runtime context
- Handles variable setting and getting
- Controls visibility of variables across scopes

## Execution Flow

1. Parse code into AST nodes
2. Interpreter receives the parse result
3. Interpreter passes statements to StatementExecutor
4. StatementExecutor:
   - For expressions, delegates to ExpressionEvaluator
   - For reason statements, delegates to LLMIntegration
   - For all operations, uses ContextManager for state
5. Results are stored or displayed as appropriate

## Error Handling

- Each component handles its own errors
- Errors are wrapped with context information
- A consistent error handling pattern is used throughout
- Error utilities are shared across components

## Hook System

- Hooks are maintained for backward compatibility
- Program-level hooks are managed by the Interpreter
- Statement-level hooks are executed by StatementExecutor
- Expression-level hooks are executed by ExpressionEvaluator
