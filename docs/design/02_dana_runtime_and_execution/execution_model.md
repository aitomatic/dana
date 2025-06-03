# Dana Execution Model

## 1. Overview

The execution model in OpenDXA defines how agents process tasks using the Dana language. Dana (Domain-Aware NeuroSymbolic Architecture) provides an imperative programming model that combines domain expertise with LLM-powered reasoning to achieve complex objectives.

This document outlines the core components and flow of Dana program execution.

## 2. Core Execution Components

*   **Dana Language**:
    *   An imperative programming language with a Python-like syntax.
    *   Features explicit state management through scopes (`local:`, `private:`, `public:`, `system:`).
    *   Includes built-in functions for common tasks and a core `reason()` function for LLM interaction.
    *   Supports user-defined functions and structs.

*   **Dana Interpreter**:
    *   Executes Dana programs by processing an Abstract Syntax Tree (AST) generated from the source code.
    *   Manages the `SandboxContext` which holds the state for all scopes.
    *   Resolves function calls through a `FunctionRegistry`.
    *   Handles runtime errors and their propagation.

*   **`SandboxContext` (Runtime Context)**:
    *   The central container for all state variables, organized by scopes (`local:`, `private:`, `public:`, `system:`). See `01_dana_language_specification/state_and_scopes.md` for details.
    *   Provides access to registered resources (tools, APIs).
    *   Facilitates progress tracking and can be involved in error information storage.

*   **Function Registry**:
    *   A central repository for all callable functions, whether built-in, core, user-defined in Dana, or Python functions exposed to Dana.
    *   Handles the lookup and dispatch of function calls made during program execution.

## 3. Execution Flow Steps

A typical execution flow for a Dana program involves:

1.  **Request Interpretation (External)**: An external system or user request is interpreted, often leading to an objective that a Dana program can fulfill.
2.  **Program Acquisition/Generation**: The Dana program to be executed is either retrieved (e.g., from a file, a knowledge base) or generated (e.g., by an LLM planner or a transcoder from natural language).
3.  **Context Initialization**: A `SandboxContext` is created and initialized. This includes populating the `private:`, `public:`, and `system:` scopes with relevant initial data. The `local:` scope typically starts empty for the main program body.
4.  **Parsing**: The Dana source code is parsed into an Abstract Syntax Tree (AST).
5.  **Interpretation/Execution**: The Dana Interpreter traverses the AST:
    *   Statements are executed sequentially.
    *   Expressions are evaluated.
    *   Variable assignments update the appropriate scope in the `SandboxContext`.
    *   Function calls are resolved via the Function Registry and executed. If a function is user-defined in Dana, a new (potentially nested) execution context might be established for it, inheriting or linking scopes as per design (e.g., `local:` scope is new for each function call).
    *   Control flow statements (`if`, `while`) alter the execution path based on conditions.
6.  **Resource Interaction**: If the Dana program calls functions that are backed by external resources (e.g., tools, APIs, LLMs via `reason()`), the interpreter or the function implementation itself interacts with these resources, passing necessary data from the `SandboxContext`.
7.  **State Modification**: Throughout execution, the Dana program reads from and writes to the various scopes in the `SandboxContext`, reflecting the ongoing state of the computation.
8.  **Result Generation & Completion**: Upon completion (or if a `return` statement is encountered in the main program body, though less common), the final state of the relevant scopes (especially `private:` or `public:`) might contain the results. If the Dana program is a function, its `return` value is passed back.
9.  **Error Handling**: If a runtime error occurs and is not caught by a `try-catch` block within the Dana program, the interpreter halts execution and reports the error. The `finally` blocks, if any, are executed.

## 4. Illustrative Dana Program Execution

```python
# Python-side setup (conceptual)
from opendxa.dana import run # Hypothetical high-level run function
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Define a Dana program
dana_program = """
# private: and public: scopes are assumed to be pre-populated in the context
log(f"Agent {private:agent_id} starting task.")

local:items_to_process = public:input_list
local:processed_results = []

for item in local:items_to_process:
    local:analysis_result = reason(f"Analyze this item: {item}", __dana_desired_type=str)
    local:processed_results.append(local:analysis_result)

private:summary = reason(f"Summarize these analyses: {local:processed_results}", __dana_desired_type=str)
log(f"Task complete. Summary: {private:summary}")
private:status = "complete"
"""

# Create and initialize context
initial_agent_state = {"agent_id": "analyzer_01", "status": "idle"}
initial_world_state = {"input_list": ["data_point_A", "data_point_B", "data_point_C"]}
context = SandboxContext(
    initial_private_state=initial_agent_state,
    initial_public_state=initial_world_state
)

# Execute the Dana program
# The 'run' function would handle parsing and interpretation
execution_outcome = run(dana_program, context)

# After execution, the context would be updated:
# context.get("private:status") would be "complete"
# context.get("private:summary") would contain the summary string
```

## 5. Key Aspects of the Execution Model

*   **Imperative and Sequential**: By default, Dana statements are executed in the order they appear, modified by standard control flow structures.
*   **Stateful**: The `SandboxContext` maintains state across operations, allowing for complex, multi-step reasoning and data manipulation.
*   **Integrated Reasoning**: The `reason()` function provides a first-class way to incorporate LLM-based reasoning directly into the imperative flow, using and updating the managed state.
*   **Explicit Scoping**: The mandatory use of scope prefixes (`local:`, `private:`, `public:`, `system:`) makes data flow and state management explicit and less prone to ambiguity.
*   **Resource Abstraction**: Functions can abstract interactions with underlying tools and resources, which are managed by the OpenDXA framework but invoked from Dana code.

This execution model is designed to provide a balance of clear, deterministic control flow with the flexibility of LLM-driven adaptive reasoning, all within a structured and stateful environment. 