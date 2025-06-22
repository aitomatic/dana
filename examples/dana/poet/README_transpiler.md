# POET Transpiler Examples

This directory contains examples demonstrating the enhanced POET transpiler implementation that generates real P→O→E (Perceive, Operate, Enforce) phases.

## New Examples (Phase 1 Implementation)

### 05_mathematical_operations.na
Demonstrates Use Case A with comprehensive mathematical function enhancement:
- `safe_divide()` - Division with automatic zero-check
- `safe_sqrt()` - Square root with domain validation
- `safe_log()` - Logarithm with automatic validation
- `calculate_percentage()` - Percentage with business rules
- `stable_calculation()` - Complex math with stability checks

Key features demonstrated:
- Division by zero caught in Perceive phase (not runtime error)
- NaN and infinity input detection
- Domain-specific mathematical constraints
- Numerical stability monitoring
- Automatic retry logic

### 06_poet_transpiler_demo.na
Shows the before/after transformation of POET transpilation:
- Visual demonstration of P→O→E phases
- Comparison of simple function vs enhanced version
- Real test cases showing validation in action
- Benefits of automatic enhancement

## Running the Examples

```bash
# Run mathematical operations examples
uv run python -m opendxa.dana.exec.dana examples/dana/poet/05_mathematical_operations.na

# Run transpiler demonstration
uv run python -m opendxa.dana.exec.dana examples/dana/poet/06_poet_transpiler_demo.na
```

## What POET Transpiler Adds

For a simple function like:
```python
@poet(domain="mathematical_operations", retries=2)
def safe_divide(a: float, b: float) -> float:
    return a / b
```

POET automatically generates:

### 1. Perceive Phase
- Type validation: `isinstance(a, (int, float, complex))`
- NaN detection: `math.isnan(a)`
- Infinity check: `math.isinf(a)` 
- Range validation: `abs(a) > 1e100`
- **Division by zero**: `if 'b' == param_name and param_value == 0`

### 2. Operate Phase
- Retry logic with configurable attempts
- Exponential backoff for failures
- Numerical stability checks
- Underflow/overflow detection
- Operation metadata tracking

### 3. Enforce Phase
- Output validation (not None, NaN, or Inf)
- Business rule enforcement
- Domain-specific result constraints
- Validation metadata generation

## Key Benefits

1. **Write simple code, get production reliability**
2. **Errors caught early** - Division by zero detected in validation, not runtime
3. **Domain intelligence** - Mathematical constraints automatically applied
4. **No boilerplate** - Enhancement happens transparently
5. **Consistent behavior** - All functions get same reliability features

## Testing

Unit tests for the transpiler are in:
```
tests/dana/poet/test_transpiler.py
```

Run tests with:
```bash
uv run pytest tests/dana/poet/test_transpiler.py -v
```