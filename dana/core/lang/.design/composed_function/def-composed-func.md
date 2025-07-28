# Declarative Function Composition in Dana (Comprehensive Design)

---

## 0. Quick Summary & Examples

Dana supports concise, inspectable function composition with clear signatures and IDE support. You can now write:

```dana
# Explicit signature (required)
def pipeline(data: dict) = x | y | z
def pipeline() = x | y | z  # No parameters
```
- Parameters must be explicitly specified (parentheses are required).
- Docstrings are supported above the definition, as in Python.

### Signature Table

| Syntax Example                        | Parameter Signature         |
|----------------------------------------|----------------------------|
| `def pipeline(x: int) = ...`           | `x: int`                   |
| `def pipeline() = ...`                 | No parameters              |

> **Note:** For maximum clarity and IDE support, always specify parameters explicitly. The grammar requires parentheses even when no parameters are needed.

---

## 1. Problem & Motivation

### 1.1. The Old Pattern
```dana
pipeline = f1 | f2 | f3  # ❌ No clear parameter signature, poor IDE/debugging
```
- No inspectable parameter signature
- Poor IDE support (no autocomplete)
- Difficult debugging (no clear function name in stack traces)
- No documentation place
- Ambiguity between data assignment and function composition

### 1.2. Goals
- Enable ergonomic, inspectable, and well-documented function composition in Dana.
- Support explicit signatures for composed functions.
- Remove ambiguity and runtime complexity from ad-hoc pipeline assignments.

---

## 2. Requirements

### 2.1. Functional
- **Clear Parameter Signature:** Functions must have explicit, inspectable parameter names, types, and defaults.
- **Documentation Support:** Must support docstrings for self-documentation.
- **IDE Integration:** Must work with autocomplete, type checking, and debugging.
- **Expressiveness:** Must maintain the power of pipe/parallel composition.
- **Syntax Removal:** Remove ad-hoc pipeline assignment syntax to eliminate ambiguity.
- **Function Composition Only:** Only support function composition expressions, not arbitrary expressions.

### 2.2. Non-Functional
- **Simplicity:** KISS principle—avoid complex grammar changes.
- **Performance:** No runtime overhead for signature resolution.
- **Maintainability:** Clean, understandable implementation.
- **Consistency:** Follow Dana's existing patterns and conventions.

---

## 3. Rationale & Trade-offs

- **Clarity:** Named, inspectable functions with explicit signatures.
- **IDE/Debugging:** Full support for autocomplete, type checking, and docstrings.
- **No ambiguity:** Ad-hoc pipeline assignments (e.g., `pipeline = x | y | z`) are deprecated in favor of `def`.
- **Trade-off:** Requires explicit parameter specification, but provides excellent tooling support and maintainability.

---

## 4. Technical Architecture

### 4.1. Syntax & Grammar
```lark
declarative_function_assignment: "def" NAME "(" [parameters] ")" ["->" basic_type] "=" expr
```
- Parameter list is required (parentheses are mandatory).
- **Currently, any expression is allowed on the right-hand side for backward compatibility.**
- **Future:** Restrict to function composition expressions only (see "Future Work").
- Arbitrary expressions (e.g., `x + 1`, `if ...`, comprehensions) are **not** recommended and will be disallowed in the future.

#### Supported Patterns
```dana
# Sequential composition
def seq_func(x: int) = f1 | f2 | f3

# Parallel composition
def par_func(x: int) = [f1, f2, f3]

# Mixed composition
def mixed_func(x: int) = f1 | [f2, f3] | f4

# Function calls with arguments
def call_func(x: int) = f1(arg1) | f2(arg2, arg3)

# No parameters
def no_params() = f1 | f2 | f3
```

#### Not Supported (but currently allowed for backward compatibility)
```dana
def wrong_func() = x + 1                    # ❌ Arbitrary expression
def wrong_func() = f"Value: {x}"           # ❌ Arbitrary expression
def wrong_func() = if x > 0: x else 0      # ❌ Conditional expression
def wrong_func() = [x * 2 for x in data]  # ❌ List comprehension
```
> **Note:** These are currently accepted by the parser for backward compatibility, but will be disallowed in a future release.

### 4.2. AST
```python
@dataclass
class DeclarativeFunctionDefinition:
    name: Identifier
    parameters: list[Parameter]  # May be empty (for no parameters)
    composition: Expression
    return_type: TypeHint | None = None
    docstring: str | None = None
    location: Location | None = None
```

### 4.3. Parser/Transformer
- Parameters are parsed according to the grammar (may be empty).
- The transformer validates that the right-hand side is a function composition expression (future: strict enforcement).
- Docstrings are extracted from preceding string literals if present.

### 4.4. Execution
- Parameters are used as specified in the AST node.
- Function metadata (`__name__`, `__doc__`, `__signature__`, `__annotations__`) is set for IDE/debugging.

### 4.5. Error Handling & Validation
- If the right-hand side is not a valid function composition, raise a parse-time error (future: strict enforcement).
- If a referenced function in the composition does not exist, raise a runtime error.
- If the composition contains non-function elements, raise a composition error.

---

## 5. Migration & Usage

### 5.1. Migration Path
- Replace ad-hoc pipeline assignments with `def`.
- Always specify parameters explicitly.
- Example migration:
```dana
# Old (deprecated):
pipeline = validate | clean | analyze

# New (recommended):
def pipeline(data: dict) = validate | clean | analyze
```

### 5.2. Docstrings
- Place docstrings immediately above the function definition, as in Python.

### 5.3. IDE/Tooling
- IDEs can now provide autocomplete, signature help, and docstring popups for composed functions.

### 5.4. Built-in Function Wrapper Workaround
- **Limitation:** Built-in functions like `str()` do not work directly in pipelines because they lack Dana signature metadata.
- **Workaround:** Use a wrapper function.

```dana
def to_string(x: any) -> str = str(x)
def pipeline(x: int) -> str = add_ten | to_string
```
> **Note:** This is a known limitation and may be improved in the future.

---

## 6. Testing & Validation

### 6.1. Unit Tests
- AST node creation and validation
- Grammar rule parsing (valid/invalid syntax)
- Transformer edge cases (missing params, empty composition)
- Docstring extraction from various positions
- Error handling for invalid composition

### 6.2. Integration & Functional Tests
- End-to-end pipeline testing with actual function compositions
- Complex scenarios with multiple parameters and type validation
- Error handling and edge cases
- IDE signature inspection

### 6.3. Example Test Cases
```python
def test_declarative_function_with_parameters():
    def add_ten(x: int) -> int: return x + 10
    add_ten.parameters = ["x"]
    context.set("local:add_ten", add_ten)
    node = DeclarativeFunctionDefinition(
        name=Identifier("pipeline"),
        parameters=[Parameter("x", TypeHint("int"))],
        composition=Identifier("add_ten"),
        return_type=None
    )
    result = executor.execute_declarative_function_definition(node, context)
    assert callable(result)
    assert result(5) == 15
    import inspect
    sig = inspect.signature(result)
    assert "x" in sig.parameters
```

#### Type Validation Example
```dana
def ensure_int(x: any) -> int = int(str(x))
def ensure_positive(x: int) -> int = x

def format_positive(x: int) -> str = f"Positive number: {x}"
def validation_pipeline(x: any) -> str = ensure_int | ensure_positive | format_positive
```

#### Built-in Function Wrapper Example
```dana
def to_string(x: any) -> str = str(x)
def pipeline(x: int) -> str = add_ten | to_string
```

---

## 7. Error Scenarios & Edge Cases

- **Non-function in composition:** Raise composition error.
- **Invalid right-hand side (not a composition):** Raise parse error (future: strict enforcement).
- **Signature mismatch at call time:** Raise TypeError as usual.
- **Docstring missing:** No docstring attached.
- **Return type inference:** Not yet implemented; always `object` unless specified.
- **Interpreter context issues:** Some complex examples may have context problems (low impact, see implementation_status.md).

---

## 8. Extensibility & Future Work

- **Restrict to function compositions:** Add validation to only allow function composition expressions (planned).
- **Built-in function support:** Improve pipeline support for built-in functions (planned).
- **Return type inference:** Infer return type from first function in the pipeline (planned).
- **IDE signature preview:** Show signatures in IDEs for all definitions.
- **Decorator support:** Allow decorators on declarative functions (future).
- **Composition templates:** Support reusable composition patterns.
- **Performance optimizations:** Compile-time composition optimization, lazy evaluation, caching.
- **Security review:** Ensure no unsafe code execution in composition.

---

## 9. References & Related Files
- [functions_and_polymorphism.md](../../../docs/reference/01_dana_language_specification/functions_and_polymorphism.md)
- [dana_grammar.lark](../../parser/dana_grammar.lark)
- [assignment_transformer.py](../../parser/transformer/statement/assignment_transformer.py)
- [statement_executor.py](../../interpreter/executor/statement_executor.py)
- [test_declarative_function_execution.py](../../../../tests/unit/core/lang/interpreter/test_declarative_function_execution.py)
- [Migration Guide](TBD)

---

## 10. Change Log
- **2024-06:** Initial design, implementation, and test coverage for declarative function composition.
- **2024-07:** Added comprehensive error handling, migration notes, and extensibility section.

---

This design enables ergonomic and robust function composition in Dana, with clear migration and extension paths. It is concise, but retains all key technical and rationale details for maintainers and users. 