# DANA Language Examples

This directory contains examples demonstrating different aspects of the DANA language.

## Directory Structure

```
examples/dana/
├── run.py              # Example runner
└── dana/              # DANA source files
    ├── basic_assignments.dana    # Basic variable assignments
    ├── syntax_errors.dana        # Syntax error handling
    └── multiple_scopes.dana      # Multiple scope usage
```

## Available Examples

1. `dana/basic_assignments.dana`
   - Basic variable assignments
   - Different value types (integers, strings, negative numbers)
   - Comment handling
   - Single scope usage

2. `dana/syntax_errors.dana`
   - Various syntax errors
   - Error messages with line numbers
   - Parser's error recovery behavior
   - Common mistakes to avoid

3. `dana/multiple_scopes.dana`
   - Using different scopes for organizing data
   - Mixing different types of values
   - Hierarchical state organization
   - JSON representation

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
