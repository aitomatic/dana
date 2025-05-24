<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# Dana Function Calling System: Design & Implementation

> **"Be conservative in what you do, be liberal in what you accept from others."**  
> — Postel's Law

> **Dana Sandbox Operating Model:**  
> Give users the best of fault-tolerance and precision/determinism, using Predict-and-Error Correct as a core principle.

---

## 1. Overview & Philosophy
- Dana aims for a simple, robust, and extensible function system.
- Prioritize user experience (magic, error-correcting, but deterministic when needed).
- Support both Dana-native and Python functions, with seamless integration.

---

## 2. Dana Function Mechanisms (from simplest to advanced)

### 2.1 Local Dana Functions (No Import)
- Most common: functions defined and called in the same Dana file.
```dana
func double(x):
    return x * 2
result = double(5)
```

### 2.2 Importing Dana Modules
- Use `import "module.na"` (global) or `import "module.na" as ns` (namespaced).
```dana
import "my_utils.na" as util
result = util.double(10)
```
- Extension `.na` triggers Dana module import.

### 2.3 Importing Python Modules
- Use `import "module.py"` (global) or `import "module.py" as ns` (namespaced).
```dana
import "my_python_module.py" as py
sum = py.add(1, 2)
```
- Extension `.py` triggers Python module import and automatic function registration.

---

## 3. Function Registry & Dispatch
- Unified registry for all callable functions (Dana and Python).
- Python functions are registered automatically on import (no decorator/boilerplate needed).
- Namespacing via `as` avoids collisions; global import is available for simplicity.
- Registry uses a singleton pattern for global access.

---

## 4. Signature Adaptation & Argument Binding
- At call time, the registry inspects the function signature and binds arguments from Dana code and context.
- Dana-aware Python functions (first arg `context`) get the Dana context injected.
- Pure Python functions get only the provided arguments.
- In the future, a context-mapping layer (Predict-and-Error Correct) can auto-fill arguments using name/type matching or LLM-powered inference.

---

## 5. Grammar & Import Syntax
- Import statements use unquoted module names: `import foo.py`
- Extension determines import type: `.py` for Python, `.na` for Dana.
- `as` provides namespacing; omitting it imports functions globally.
- Example grammar rule:
  ```
  import_stmt : "import" module_path ("as" IDENTIFIER)?
  ```

---

## 6. Variable Passing Policy
| Scope    | Default Passing Policy         | Rationale |
|----------|-------------------------------|-----------|
| public   | Automatically available        | Safe, enables "magic" UX |
| system   | Opt-in/allowlist               | Useful for context (timezone, etc.), but may be sensitive |
| private  | Explicitly allowed             | User/session-specific, sensitive |
| local    | Explicitly allowed             | Temporary, function/block-specific |
- All public variables are available to every function call.
- Only allowlisted system variables are auto-passed; others require explicit opt-in.
- Private/local variables are never passed unless explicitly requested.

---

## 7. Security, Auditability, and Best Practices
- Default to minimal, safe context passing.
- Allow opt-in for more sensitive scopes.
- Log/audit context passing for traceability and debugging.
- Use namespacing (`as`) to avoid collisions in larger projects.

---

## 8. Extensibility & Future Enhancements
- Centralize argument binding logic for easy enhancement.
- Predict-and-ErrorCorrect: LLM-powered or heuristic context-to-argument mapping.
- Allow both caller and callee to provide hints (decorators, flags) for context/variable injection.
- Make P&E magic opt-in at first, with clear override/opt-out mechanisms.
- Policy configuration: Allow admins to set global or per-function context policies.

---

## 9. System-Level Example Flows

### 9.1 Dana Import Triggers Python Function Registration
- Dana code: `import "my_python_module.py" as py`
- Interpreter loads the Python module, introspects for functions, and registers them as `py.funcname`.
- Dana can now call `py.funcname(...)`.

### 9.2 Function Call Dispatch
- Dana code: `result = py.add(x, y)`
- Registry looks up `py.add`, inspects signature, injects context if needed, binds arguments, and calls the function.

---

## 10. Implementation Notes
- Use `inspect.signature` for signature adaptation.
- Centralize all argument/context binding in the registry for future extensibility.
- Registry uses a singleton pattern for global access.
- Decorator support is optional for advanced users, but not required for Dana import.

---

## 11. Appendix: Example Code and Pseudocode

**Python module (my_python_module.py):**
```python
def add(a, b):
    return a + b

def reason(context, prompt):
    return f"You asked: {prompt}"
```

**Dana code:**
```dana
import "my_python_module.py" as py
sum = py.add(1, 2)
answer = py.reason("What is the capital of France?")

func double(x):
    return x * 2
result = double(5)
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>