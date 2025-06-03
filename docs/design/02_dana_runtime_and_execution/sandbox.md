<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[▲ 02. Dana Runtime and Execution](../README.md)

| [← Interpreter](./interpreter.md) | [REPL →](./repl.md) |
|---|---|

# Dana Secure Sandbox and Runtime

## 1. Overview

The Dana runtime is designed to securely and robustly process and execute Dana code from various sources, such as scripts and interactive REPL sessions. All stages of code processing and execution are intended to be contained within a conceptual "Sandbox" environment, which provides isolation, security, resource management, and a well-defined execution context (`SandboxContext`).

This document outlines the overall runtime flow and the role of the sandbox.

## 2. Runtime Flow within the Sandbox

At a high level, the Dana runtime flow involves several key stages:

1.  **Parsing**: Source code is parsed into an Abstract Syntax Tree (AST). (See [Parser Details Placeholder](../../01_dana_language_specification/parser.md) and [Grammar Details](../../01_dana_language_specification/grammar.md)).
2.  **AST Transformation (Optional)**: The AST might undergo transformations for optimization or to prepare it for execution.
3.  **Type System Interaction (Optional)**: Dana is dynamically typed, but type hints can inform behavior (e.g., polymorphism, AI assistance). (See [Type System and Casting](./type_system_and_casting.md)).
4.  **Interpretation**: The [Dana Interpreter](./interpreter.md) executes the AST, managing state within the `SandboxContext`.
5.  **Execution Model**: The overall process is governed by the [Dana Execution Model](./execution_model.md).

## 3. Flow Diagram

```mermaid
graph TB
    subgraph UserInput
        direction LR
        SCRIPT[Dana Script] 
        REPL_INPUT[REPL Input]
    end

    UserInput --> SANDBOX_ENV[Sandbox Environment]

    subgraph SANDBOX_ENV [Dana Runtime / Sandbox]
        direction LR
        PARSER[1. Parser] --> AST_GEN[[AST]]
        AST_GEN --> TRANSFORMER(2. AST Transformer 
Optional)
        TRANSFORMER --> AST_PROC[[Processed AST]]
        AST_PROC --> TYPE_INFO([3. Type Info 
(Hints, Desired Type)])
        TYPE_INFO --> INTERPRETER[4. Interpreter]
        INTERPRETER --> EXEC_CONTEXT[SandboxContext]
        INTERPRETER --> FUNC_REG[Function Registry]
        EXEC_CONTEXT <--> INTERPRETER
        FUNC_REG <--> INTERPRETER
    end

    INTERPRETER --> PROGRAM_OUTPUT[[Program Output / Effects]]

    style SCRIPT fill:#cde4ff
    style REPL_INPUT fill:#cde4ff
    style AST_GEN fill:#e1f5fe
    style AST_PROC fill:#e1f5fe
    style PROGRAM_OUTPUT fill:#d4edda
    style EXEC_CONTEXT fill:#fff9c4
    style FUNC_REG fill:#ffe0b2
```

## 4. Stages Explained

-   **Input (Script / REPL)**: Entry points for user-provided Dana code.
-   **Sandbox Environment / Dana Runtime**: The overarching container and process that manages code processing and execution.
    -   **Parser**: Converts source code into an Abstract Syntax Tree (AST) based on the Dana [Grammar](../../01_dana_language_specification/grammar.md).
    -   **AST Transformer (Optional)**: Modifies the AST for various purposes (e.g., optimization, desugaring complex syntax).
    -   **Type Information**: While Dana is dynamically typed, the system can use type hints or caller-specified desired types (via `__dana_desired_type` in `SandboxContext`) to guide execution, especially for polymorphic functions and LLM interactions. See [Type System and Casting](./type_system_and_casting.md) and [Functions and Polymorphism](../../01_dana_language_specification/functions_and_polymorphism.md).
    -   **Interpreter**: The core component that executes the AST. It interacts with the `SandboxContext` for state and the `FunctionRegistry` for function calls. See [Interpreter](./interpreter.md).
    -   **`SandboxContext`**: Holds all runtime state, including variables across different scopes (`local:`, `private:`, `public:`, `system:`), registered resources, and potentially the `__dana_desired_type`. See [State and Scopes](../../01_dana_language_specification/state_and_scopes.md) and [Execution Model](./execution_model.md).
    -   **Function Registry**: Manages all available functions (built-in, user-defined Dana, Python-backed). See [Functions and Polymorphism](../../01_dana_language_specification/functions_and_polymorphism.md).
-   **Program Output / Effects**: The results or side effects (e.g., state changes in `SandboxContext`, external API calls, logged messages) produced by running the program.

## 5. Key Goals of the Sandbox Approach

-   **Controlled Execution**: Ensures that all Dana code, regardless of origin, is processed and executed within a managed and observable environment.
-   **State Management**: Centralizes state via `SandboxContext`, making it explicit and manageable.
-   **Resource Management (Future)**: The sandbox concept can be extended to manage and limit access to system resources (CPU, memory, network) if Dana execution is exposed to less trusted environments.
-   **Security (Future)**: For scenarios involving code from untrusted sources, the sandbox would be critical for preventing malicious actions by restricting capabilities.
-   **Consistency**: Both REPL interactions and script executions share the same runtime pipeline, ensuring consistent behavior.

This document provides a high-level view. Detailed designs for components like the Parser, Interpreter, `SandboxContext`, and Type System are covered in their respective documents.

---
*Self-reflection: The term "Sandbox" is used here more as a conceptual wrapper for the entire runtime environment rather than a strict, isolated process like a browser sandbox, though it can evolve towards stricter isolation if needed. The focus is on controlled execution via the `SandboxContext` and interpreter. Links to parser and transformer specifics are placeholders.* 