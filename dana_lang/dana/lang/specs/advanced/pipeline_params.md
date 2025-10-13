**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 0.9.0  
**Status:** Design

# Advanced Pipeline Parameter Passing for Dana Declarative Functions

## Overview

This document describes the implementation of advanced parameter passing mechanisms for Dana's declarative function composition feature. The system provides three powerful ways to control how data flows through pipeline stages:

1. **Implicit First Parameter** - Default behavior where pipeline result is automatically passed as the first argument
2. **Explicit Placement with `$$`** - Explicit control over where the pipeline value is placed in function arguments
3. **Named Parameter Capture with `as`** - Capture intermediate results with names for reuse in later pipeline stages

## Grammar Changes

### Updated Grammar Rules

```lark
// Pipeline expressions now support named stages from the start
pipe_expr: pipeline_stage (PIPE pipeline_stage)*

// Each pipeline stage can optionally capture its result with a name
pipeline_stage: or_expr ["as" NAME] -> pipeline_stage_expr

// Placeholder expression for explicit parameter placement
placeholder: DOLLAR_DOLLAR -> placeholder_expression

// Token definition
DOLLAR_DOLLAR: "$$"
```

## AST Nodes

### New AST Node: NamedPipelineStage

```python
@dataclass
class NamedPipelineStage:
    """A pipeline stage with an optional name capture (expr as name)."""
    expression: Expression
    name: str | None = None  # If present, capture result with this name
    location: Location | None = None
```

### Existing AST Node: PlaceholderExpression

```python
@dataclass
class PlaceholderExpression:
    """A placeholder expression representing the $$ symbol in pipeline operations."""
    location: Location | None = None
```

## Execution Semantics

### 1. Implicit First Parameter (Default)

When a function is called in a pipeline without `$$` placeholder, the pipeline value is automatically passed as the first argument:

```dana
# Pipeline definition
def process(x) = add_ten | multiply_by(2) | format_result("Result: ")

# Execution flow:
# x=5 → add_ten(5)=15 → multiply_by(15, 2)=30 → format_result("Result: ", 30)="Result: 30"
```

### 2. Explicit Placement with `$$`

The `$$` placeholder allows explicit control over where the pipeline value is placed:

```dana
# Place pipeline value in specific positions
def process(x) = add_ten | multiply_by($$, 3) | format_result("Value: ", $$, "!")

# Execution flow:
# x=5 → add_ten(5)=15 → multiply_by(15, 3)=45 → format_result("Value: ", 45, "!")
```

**Important**: When `$$` is used, implicit first parameter passing is disabled for that function call.

### 3. Named Parameter Capture

The `as` syntax captures intermediate results for later use:

```dana
# Capture and reuse intermediate values
def process(x) = add_ten as base | multiply_by(2) as doubled | format_result(base, doubled)

# Execution flow:
# x=5 → add_ten(5)=15 (saved as 'base')
#     → multiply_by(15, 2)=30 (saved as 'doubled')  
#     → format_result(15, 30)
```

### Pipeline Context

Each pipeline execution maintains its own context for named captures:
- Named captures are scoped to the pipeline execution
- They do not affect the outer execution context
- Names can shadow outer variables without side effects
- Forward references are not allowed (using a name before it's captured results in an error)

## Implementation Details

### Parser/Transformer Updates

The expression transformer handles the new syntax:
- `pipeline_stage_expr` rule creates `NamedPipelineStage` nodes
- `placeholder_expression` rule creates `PlaceholderExpression` nodes
- Pipeline stages are uniformly processed, allowing `as` syntax on any stage

### Execution Engine Updates

The expression executor implements the parameter passing logic:

1. **Pipeline Context Management**
   - Each pipeline execution creates a `pipeline_context` dictionary
   - Named captures are stored in this context
   - Context is passed through all pipeline stages

2. **Argument Resolution**
   - Arguments are scanned for `PlaceholderExpression` nodes
   - Named variables are resolved from pipeline context first
   - `$$` placeholders are replaced with the current pipeline value

3. **Implicit Parameter Logic**
   - If no `$$` is found in arguments, current value is prepended
   - This maintains backward compatibility with existing pipelines

## Usage Examples

### Complex Business Logic

```dana
def calculate_invoice(price) = 
    multiply(1) as original |              # Capture original price
    apply_discount($$, 20) as discounted | # 20% discount
    calculate_tax(discounted, 0.08) as tax | # 8% tax
    add(discounted, tax) as total |        # Final total
    format_invoice(original, discounted, tax, total)
```

### Data Transformation

```dana
def transform_data(value) =
    normalize as normalized |
    validate($$) as validation_result |
    enrich(normalized, validation_result) |
    format_output("Processed", $$)
```

### Error Handling

```dana
def safe_process(value) =
    validate as is_valid |
    process($$) if is_valid else error("Invalid input") |
    log_result($$, is_valid)
```

## Testing Strategy

### Unit Tests
- Parser tests verify correct AST generation
- Execution tests verify parameter passing behavior
- Error cases test proper error handling

### Functional Tests
- Separate test files for each mechanism
- Complex scenarios combining all mechanisms
- Real-world use case examples

## Future Enhancements

1. **Conditional Execution** - Support for conditional pipeline stages based on captured values
2. **Pipeline Composition** - Allow pipelines to be composed and reused as building blocks
3. **Type Checking** - Static type checking for pipeline parameter compatibility
4. **Performance Optimization** - Optimize pipeline execution for common patterns