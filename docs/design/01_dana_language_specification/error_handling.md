# Dana Error Handling

This document outlines the design for error handling within the Dana language and its runtime environment. Effective error handling is crucial for building robust and reliable agentic systems.

## 1. Philosophy

Dana's error handling philosophy aims to be:

*   **Explicit**: Errors should not pass silently unless explicitly handled.
*   **Informative**: Error messages should be clear, provide context, and guide the developer or agent towards a solution.
*   **Recoverable (where possible)**: The system should support mechanisms for catching and recovering from errors, allowing agents to adapt or retry.
*   **Consistent**: Error handling patterns should be consistent across built-in functions, user-defined functions, and the runtime itself.

## 2. Types of Errors

Dana programs can encounter several types of errors:

1.  **Parse Errors (Syntax Errors)**:
    *   Occur when Dana code violates the language grammar (e.g., incorrect syntax, mismatched parentheses, invalid indentation).
    *   Detected by the parser before execution begins.
    *   Typically halt execution immediately and report the location and nature of the syntax error.

2.  **Runtime Errors**:
    *   Occur during the execution of a Dana program.
    *   Examples:
        *   **Type Errors**: Performing an operation on an incompatible data type (e.g., `local:num = "text" + 5` if auto-coercion to string isn't applicable or fails).
        *   **Name Errors**: Referencing an undefined variable or function.
        *   **Index Errors**: Accessing a list element with an out-of-bounds index.
        *   **Key Errors**: Accessing a dictionary with a non-existent key.
        *   **ZeroDivisionError**: Dividing by zero.
        *   **Scope Errors**: Attempting to access a variable in a scope where it's not defined or accessible according to scope rules (though often manifest as NameErrors).
        *   **Resource Errors**: Errors originating from external resources or tools that a Dana function interacts with (e.g., API call failure, file not found by a resource).
        *   **Assertion Errors**: If Dana includes an `assert` statement, failures would raise this.
        *   **Custom Errors**: User-defined functions or modules might define and raise specific error conditions.

3.  **IPV (Infer-Process-Validate) Errors**:
    *   Specific to IPV-enabled functions (like `reason()`).
    *   Can occur during the `infer`, `process`, or `validate` phases.
    *   Examples: Failure to generate a coherent plan, LLM call failure, validation of LLM output against `__dana_desired_type` fails.

## 3. Error Reporting

When an unhandled error occurs:

*   **Message**: A clear message describing the error.
*   **Type**: The type of error (e.g., `TypeError`, `NameError`, `ResourceError:APIError`).
*   **Location**: The file name, line number, and relevant code snippet where the error occurred (if applicable).
*   **Traceback (Stack Trace)**: For runtime errors, a traceback showing the sequence of function calls leading up to the error.
*   **Contextual Information**: Potentially relevant state variables or parameters involved in the error, aiding diagnosis (care must be taken not to expose sensitive private: data in general error reports).

## 4. Error Handling Mechanisms

### 4.1. `try-catch-finally` Blocks (Proposed)

To allow Dana programs to handle errors gracefully, a `try-catch-finally` mechanism, similar to that in Python or JavaScript, is proposed.

**Syntax (Conceptual):**

```dana
try:
    # Code that might raise an error
    local:risky_value = 10 / local:divisor
    print(local:risky_value)
catch <ErrorType1> as local:err1:
    # Handle ErrorType1 specifically
    log(f"Caught specific error: {local:err1.type} - {local:err1.message}")
    # local:err1 would be an object/struct containing error details
catch <ErrorType2> as local:err2:
    # Handle ErrorType2 specifically
    log(f"Caught another error: {local:err2.message}")
catch as local:general_error: # Catch any other error (if specific types not matched)
    log(f"An unexpected error occurred: {local:general_error.message}")
finally:
    # Code that always executes, regardless of whether an error occurred or was caught
    print("Execution of try block finished.")
```

*   **`try`**: Contains the code that might produce an error.
*   **`catch <ErrorType> as <variable>`**: Catches errors of a specific type (or its subtypes). The error object/struct is assigned to `<variable>`.
*   **`catch as <variable>`**: A general catch block if no specific error type is provided or matched.
*   **`finally`**: Contains code that is always executed after the `try` and any `catch` blocks, whether an error occurred or not. Useful for cleanup operations.
*   **Error Object/Struct**: The `local:err1` variable would ideally be a struct containing fields like `type` (e.g., "ZeroDivisionError"), `message`, `traceback`, etc.

### 4.2. `raise` Statement (Proposed)

To allow user-defined functions to signal errors.

**Syntax (Conceptual):**

```dana
def process_payment(amount: float):
    if amount <= 0:
        # Create an error object/struct (details TBD)
        local:error_details = DanaError(type="ValueError", message="Payment amount must be positive.")
        raise local:error_details
    # ... process payment ...
```
Dana would need a way to define or construct error objects/structs, perhaps with a built-in `DanaError` type or similar.

## 5. Error Propagation

*   If an error is raised within a `try` block, the interpreter looks for a matching `catch` block within the same `try-catch-finally` structure.
*   If a match is found, the corresponding `catch` block is executed.
*   If no matching `catch` block is found in the current function, the error propagates up the call stack to the calling function.
*   If the error propagates all the way to the top-level of the Dana program without being caught, the program terminates, and the error is reported to the user or the orchestrating system.
*   The `finally` block is executed regardless of whether an error was caught or if it propagates further.

## 6. Built-in Error Types (Examples)

Dana should define a hierarchy of built-in error types. Examples:

*   `Error` (base type for all Dana errors)
    *   `ParseError`
    *   `RuntimeError`
        *   `TypeError`
        *   `NameError`
        *   `IndexError`
        *   `KeyError`
        *   `ValueError`
        *   `ZeroDivisionError`
        *   `AssertionError`
        *   `ResourceError` (base for errors from resources)
            *   `ResourceError:APIError`
            *   `ResourceError:FileNotFound`
        *   `IPVError`
            *   `IPVError:ValidationFailure`

## 7. Integration with IPV

The IPV (Infer-Process-Validate) pattern has its own error handling within its phases. Errors from the IPV process (e.g., LLM unavailability, validation failure) should be catchable by the Dana program calling the IPV-enabled function. The `validate_phase` of IPV is particularly crucial for catching and transforming LLM outputs that don't conform to expectations, potentially raising a specific `IPVError:ValidationFailure`.

## 8. Open Questions & Future Considerations

*   **Defining Custom Error Types**: Should users be able to define their own error types using `struct`s?
*   **Error Logging vs. Catching**: Standardizing how errors are logged versus caught and handled.
*   **Stack Trace Detail**: What level of detail is appropriate for Dana stack traces, balancing debuggability with simplicity?
*   **Asynchronous Error Handling**: If Dana introduces async operations, how will errors in those contexts be managed?

This document provides a foundational design. Further details will be refined as implementation progresses. 