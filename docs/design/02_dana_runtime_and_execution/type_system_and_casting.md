| [← POV Execution Model](./pov_execution_model.md) | [Concurrency Model →](./concurrency_model.md) |
|---|---|

# Type System and Casting

*(This document is a placeholder and needs to be populated with details about Dana's type system, dynamic typing philosophy, type hinting for AI and polymorphism, and rules for type casting, both implicit and explicit.)*

## Key Aspects to Cover:

* Dynamic Typing: Reinforce that Dana is fundamentally dynamically typed.
* Type Hints:
 * Purpose: Clarity, AI assistance, enabling polymorphism, informing IPV.
 * Syntax for type hints (e.g., `private:my_var: int`).
 * Not for static enforcement by the interpreter by default.
* Built-in Types: Refer to `data_types_and_structs.md` for the list of basic types.
* Structs as Types: How user-defined structs become types.
* Polymorphism: How type hints on function parameters enable polymorphic dispatch (see `functions_and_polymorphism.md`).
* `__dana_desired_type`:
 * Mechanism for callers to inform functions about the desired return type.
 * How it's passed (via `SandboxContext` `system:` scope).
 * Role in IPV `validate_phase`.
* Type Casting/Coercion:
 * Implicit Casting: Rules for when types are automatically converted (e.g., `int` to `float` in arithmetic operations). Aim for safety, avoid surprising implicit lossy conversions.
 * Explicit Casting: Syntax for explicit type conversions (e.g., `int(my_float_var)`, `str(my_int_var)`).
 * Allowing explicit lossy conversions (e.g., `int(3.14)` results in `3`).
 * Behavior for impossible casts (e.g., `int("hello")` - should result in an error).
 * Casting to/from `any`.
* Interaction with `instanceof` operator (if planned, or a `type()` function).
* Error Handling for Type Mismatches/Casting Failures.