# Syntax Specification - Enhanced Function Composition

## Current Syntax (Foundation)

### Sequential Composition
```dana
# Basic pipe operator (already working)
result = a | b | c
composed_func = add_ten | double | stringify
data_pipeline = 5 | add_ten | double
```

## New Syntax: Parallel Composition

### Parallel Block Syntax
```dana
# Parallel execution block using curly braces
a | b | { c1, c2, c3 } | d | e

# Real example
process_data | validate | { format_json, format_xml, format_csv } | send_response
```

### Syntax Rules (KISS Approach)

#### 1. Parallel Block Definition
- **Syntax:** `{ function1, function2, function3, ... }`
- **Minimum functions:** 2 (single function doesn't need parallel block)
- **Maximum functions:** Unlimited (practical limit based on system resources)
- **Separator:** Comma (`,`)
- **Whitespace:** Optional around commas and braces

#### 2. Valid Parallel Block Positions
```dana
# ✅ Valid: Parallel block in middle of pipeline
a | { b1, b2 } | c

# ✅ Valid: Parallel block at end
a | b | { c1, c2, c3 }

# ❌ Invalid: Parallel block at start (no input to parallelize)
{ a1, a2 } | b

# ✅ Valid: Multiple parallel blocks
a | { b1, b2 } | c | { d1, d2, d3 } | e
```

#### 3. Function Types in Parallel Blocks
```dana
# ✅ All types supported
{ builtin_func, user_func, lambda x: x * 2, composed_func }

# ✅ Mixed function types
process | { validate_data, log_event, send_notification } | finalize
```

## Grammar Extensions (BNF)

### Current Grammar
```bnf
pipe_expression := expression '|' expression
```

### Extended Grammar
```bnf
pipe_expression := expression '|' (expression | parallel_block)
parallel_block := '{' function_list '}'
function_list := function (',' function)*
function := identifier | lambda_expression | composed_function
```

## Semantic Rules

### 1. Execution Order
```dana
a | b | { c1, c2, c3 } | d
```
**Execution Flow:**
1. Execute `a`, result flows to `b`
2. Execute `b`, result flows to parallel block
3. Execute `c1`, `c2`, `c3` **simultaneously** with same input
4. Collect results as list: `[result_c1, result_c2, result_c3]`
5. Execute `d` with collected results

### 2. Parameter Passing (Phase 1 - Simple)
```dana
# Input to parallel block
upstream_result → { f1, f2, f3 }

# Each function receives the same input
f1(upstream_result)
f2(upstream_result) 
f3(upstream_result)

# Output from parallel block
downstream_func([f1_result, f2_result, f3_result])
```

### 3. Type Compatibility
```dana
# Phase 1: Simple validation
def process(data): return data * 2
def collect(results: list): return sum(results)

# ✅ Valid: collect expects list, parallel block provides list
process | { double, triple } | collect

# ❌ Invalid: String function expecting list
process | { double, triple } | "not_a_function"
```

## Examples

### 1. Basic Parallel Processing
```dana
def double(x): return x * 2
def triple(x): return x * 3
def add_ten(x): return x + 10
def sum_results(results): return sum(results)

# Parallel processing with aggregation
result = 5 | { double, triple, add_ten } | sum_results
# Flow: 5 → [10, 15, 15] → 40
```

### 2. Data Processing Pipeline
```dana
def fetch_data(id): return get_user_data(id)
def validate_email(data): return validate(data.email)
def validate_phone(data): return validate(data.phone)
def validate_address(data): return validate(data.address)
def collect_validation(results): return all(results)

# User validation pipeline
is_valid = user_id | fetch_data | { validate_email, validate_phone, validate_address } | collect_validation
```

### 3. Format Conversion
```dana
def parse_input(text): return parse(text)
def to_json(data): return json.dumps(data)
def to_xml(data): return xml_serialize(data)
def to_csv(data): return csv_serialize(data)
def package_formats(formats): return {"json": formats[0], "xml": formats[1], "csv": formats[2]}

# Multi-format output
output = user_input | parse_input | { to_json, to_xml, to_csv } | package_formats
```

## Error Cases

### 1. Syntax Errors
```dana
# Missing comma
{ func1 func2 }  # SyntaxError

# Empty parallel block  
{ }  # SyntaxError

# Single function (should use regular pipe)
{ single_func }  # Warning: unnecessary parallel block

# Unmatched braces
{ func1, func2  # SyntaxError
```

### 2. Runtime Errors (Phase 1 - Fail Fast)
```dana
def failing_func(x): raise Exception("Failed")
def working_func(x): return x * 2

# Any failure in parallel block stops execution
result = 5 | { working_func, failing_func } | collect
# → Exception: Failed (immediate failure)
```

## Implementation Notes

### 1. AST Extensions Required
- New `ParallelBlock` AST node
- Modify `BinaryExpression` to handle parallel blocks
- Update parser to recognize `{` and `}` in pipe context

### 2. Backward Compatibility
- All existing pipe operator syntax remains unchanged
- No breaking changes to current function composition
- New syntax is purely additive

### 3. Parser Priorities
```
pipe_expression := 
  | expression '|' parallel_block '|' expression  # New
  | expression '|' expression                     # Existing
```

This syntax specification provides a solid foundation for Phase 1 implementation while maintaining simplicity and extensibility for future enhancements. 