| [← User-defined Resources](./user_defined_resources.md) | [Next Section (TBD) →](../README.md) |
|---|---|

# Capability Invocation from Dana

*(This document is a placeholder. It will describe the syntax and semantics for how Dana code invokes methods on Resource instances that are available in the `SandboxContext`.)*

## Key Aspects to Detail:

* Accessing Resources in Dana:
 * How resources are made available as variables or named entities within Dana scopes (e.g., `system:my_llm_resource`, or implicitly available like `llm.chat(...)` if a default `LLMResource` is configured).
 * Namespace considerations if multiple resources of the same type exist.
* Syntax for Method Calls:
 * Standard method call syntax (e.g., `private:result = system:my_resource.method_name(arg1, arg2: val2)`).
 * Passing arguments: Positional and named arguments.
 * How Dana types are passed to Python resource methods.
* Return Values:
 * How return values from Python resource methods are translated back to Dana types.
 * Handling of complex data structures.
* Error Handling:
 * How exceptions raised by resource methods in Python are caught and represented as errors in Dana.
 * Using `try/catch` in Dana to handle resource call failures.
* Implicit Context: Does the `SandboxContext` (or parts of it) get implicitly passed to resource methods, or must all context be explicit arguments?
* The `reason()` function as a special case of capability invocation:
 * How `reason()` might abstract away direct resource interaction for common LLM tasks.
 * Relationship between `reason()` and underlying `LLMResource` calls (IPV pattern).
* Asynchronous Invocations (if Dana supports concurrency):
 * Syntax for calling resource methods asynchronously (e.g., `await system:my_resource.async_method()`).
 * How results from async calls are handled.
* Security Considerations:
 * Reiterate that all resource interactions are mediated by the Resource Abstraction Model, which can enforce policies.
* Examples:
 * Dana code snippets showing calls to various methods of the standard system resources (LLM, FileSystem, Network).
 * Example of handling a resource call failure.

*Self-reflection: Clear, consistent, and intuitive syntax for capability invocation is crucial for Dana's usability. The design should align with Dana's overall philosophy of explicitness and clarity.*