# Dana Language Examples

This directory contains examples demonstrating different aspects of the Dana language.

## Directory Structure

```
examples/dana/
├── run.py              # Example runner
└── dana/              # Dana source files
    ├── basic_assignments.dana    # Basic variable assignments
    ├── syntax_errors.dana        # Syntax error handling
    └── multiple_scopes.dana      # Multiple scope usage
```

## Available Examples

### Basic Language Features

1. `na/basic_assignments.na`
   - Basic variable assignments
   - Different value types (integers, strings, negative numbers)
   - Comment handling
   - Single scope usage

2. `na/syntax_errors.na`
   - Various syntax errors
   - Error messages with line numbers
   - Parser's error recovery behavior
   - Common mistakes to avoid

3. `na/multiple_scopes.na`
   - Using different scopes for organizing data
   - Mixing different types of values
   - Hierarchical state organization
   - JSON representation

4. `na/arithmetic_example.na`
   - Float literals and arithmetic operations
   - Mixed types and operator precedence
   - Mathematical calculations

### Built-in Functions

5. `na/builtin_functions_basic.na` ⭐ **NEW**
   - Essential collection functions: `len()`, `sum()`, `max()`, `min()`
   - Type conversion: `int()`, `round()`
   - Practical examples with grade analysis
   - Perfect for learning the most commonly used built-ins

6. `na/pythonic_builtins_demo.na` ⭐ **NEW**
   - Comprehensive demonstration of all Pythonic built-in functions
   - Collection processing: `sorted()`, `all()`, `any()`, `enumerate()`
   - Mathematical functions: `abs()`, `round()`
   - Type conversions: `int()`, `float()`, `bool()`
   - Advanced usage patterns and data analysis examples

### Advanced Features

7. `na/hybrid_math_agent.na`
   - LLM-based mathematical reasoning with validation
   - Function definitions and tool usage
   - Complex agent patterns

8. `na/reason_demo.na`
   - AI reasoning capabilities
   - Context management
   - LLM integration patterns

## Running Examples

Run all examples:
```bash
python run.py
```

Run a specific example:
```bash
python run.py dana/basic_assignments.dana
```

## Adding New Examples

1. Add new `.dana` files to the `dana/` directory
2. Use descriptive names (e.g., `expressions.dana`, `functions.dana`)
3. Test using `run.py`
