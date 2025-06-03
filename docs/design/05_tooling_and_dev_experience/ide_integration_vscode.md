| [← README](../README.md) | [REPL Enhancements →](./repl_enhancements.md) |
|---|---|

# IDE Integration (VS Code) for Dana

*(This document is a placeholder. It will outline planned and desired features for Dana language support within Visual Studio Code, aiming to provide a rich developer experience.)*

## Key Features for VS Code Integration:

*   **Syntax Highlighting**: 
    *   Accurate highlighting of Dana keywords, built-in types, literals (strings, numbers, booleans, null), comments, scopes (`private:`, `public:`, `local:`, `system:`).
    *   Distinguishing between function definitions and calls.
    *   Highlighting for struct definitions and type hints.
    *   Based on a TextMate grammar (`.tmLanguage.json` or similar).

*   **Linting and Static Analysis**: 
    *   Integration with a Dana linter (if one is developed separately or as part of the parser/compiler).
    *   Real-time feedback on syntax errors.
    *   Checks for basic semantic errors (e.g., undefined variables if determinable, scope violations if detectable statically).
    *   Style checking (e.g., consistent indentation, naming conventions).

*   **Code Snippets**: 
    *   Predefined snippets for common Dana constructs:
        *   Function definitions (`func`)
        *   Struct definitions (`struct`)
        *   Control flow (`if/else`, `for`, `while`)
        *   `try/catch` blocks
        *   Variable declarations with scopes
        *   Common resource calls (e.g., `log()`, `reason()`)

*   **Auto-Completion / IntelliSense**: 
    *   Completion for Dana keywords.
    *   Completion for variables within the current scope (requires some level of semantic understanding).
    *   Completion for built-in function names and parameters.
    *   Completion for Resource methods if resource types can be inferred.
    *   Completion for struct fields.

*   **Hover Information**: 
    *   Displaying type information (from hints or inference) for variables and function parameters/return values on hover.
    *   Showing documentation strings for functions and resources on hover.

*   **Formatting**: 
    *   Integration with a Dana code formatter (auto-formatting on save or via command).
    *   Ensuring consistent code style.

*   **Go to Definition / Find References**: 
    *   Ability to navigate from a variable usage to its definition.
    *   Find all usages of a variable, function, or struct.
    *   (Requires significant semantic analysis capabilities).

*   **Debugging Support** (More Advanced):
    *   Connecting to the Dana debugger (see `02_dana_runtime_and_execution/debugging_profiling.md`).
    *   Setting breakpoints.
    *   Stepping through code.
    *   Inspecting variables and `SandboxContext`.
    *   Requires implementation of the Debug Adapter Protocol (DAP).

*   **REPL Integration** (Conceptual):
    *   Ability to send selected Dana code from the editor to an integrated Dana REPL session.

*   **Task Integration**: 
    *   Defining VS Code tasks for common Dana operations (e.g., running a script, running tests).

## Implementation Considerations:

*   Language Server Protocol (LSP) for advanced features like auto-completion, go-to-definition, linting.
*   Developing a dedicated Dana VS Code extension.

*Self-reflection: A robust VS Code extension is critical for developer adoption and productivity. Syntax highlighting, basic linting, and snippets would be good starting points, with LSP-based features as a more advanced goal.* 