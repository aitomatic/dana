<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[▲ 02. Dana Runtime and Execution](../README.md)

| [← Sandbox](./sandbox.md) | [IPV Architecture →](./ipv_architecture.md) |
|---|---|

# Dana REPL (Read-Eval-Print Loop)

**Relevant Modules**:
- `opendxa.dana.exec.repl.repl`: The main REPL class (programmatic API)
- `opendxa.dana.exec.repl.dana_repl_app`: The user-facing CLI application

## 1. Overview

The Dana REPL (Read-Eval-Print Loop) provides an interactive command-line environment for executing Dana code snippets and, optionally, natural language statements that can be transcoded to Dana. It is a crucial tool for learning, experimenting, and debugging Dana programs.

The REPL utilizes the [Dana Parser](../../01_dana_language_specification/parser.md) (placeholder for actual parser doc) to parse input into an AST, and then the [Dana Interpreter](./interpreter.md) executes this AST. The state across REPL interactions is managed within a persistent `SandboxContext` (see [Sandbox](./sandbox.md) and [State and Scopes](../../01_dana_language_specification/state_and_scopes.md)).

## 2. Features

-   **Interactive Execution**: Directly execute Dana statements and expressions.
-   **Natural Language Transcoding**: If an LLM resource is configured, natural language input can be translated into Dana code and then executed. (Relies on a [Transcoder](../../../TODO_LINK_TRANSCODER_DESIGN.md) component - placeholder).
-   **Command History**: Recall and reuse previous commands (typically using arrow keys, via `prompt_toolkit`).
-   **Tab Completion**: Keyword-based completion for Dana syntax elements.
-   **Multiline Input**: Supports entering complex, multiline Dana statements and blocks (e.g., `if/else`, `for`, function definitions).
-   **Special Commands**: Meta-commands (e.g., prefixed with `##`) for controlling REPL behavior, such as toggling NLP mode.
-   **Persistent Context**: The `SandboxContext` persists across multiple inputs within a single REPL session, allowing variables and state to be maintained.

## 3. Usage

### Starting the REPL CLI

Typically, the REPL is started via a command-line script:

```bash
python -m opendxa.dana.exec.repl.dana_repl_app
```

### Programmatic API

The REPL functionality can also be accessed programmatically:

```python
from opendxa.dana.exec.repl.repl import REPL
from opendxa.dana.sandbox.sandbox_context import SandboxContext # Assuming direct context management

# Initialize context (it persists for the REPL session)
context = SandboxContext()

repl_engine = REPL(context=context)

# Execute a Dana snippet
result_info = repl_engine.execute("private:x = 42\nlog(private:x)")

# result_info might contain execution status, output, or errors
print(f"Execution Status: {result_info.status}")
if result_info.value is not None:
    print(f"Returned Value: {result_info.value}")
if result_info.output_log:
    print(f"Logged Output: {result_info.output_log}")

# Example of getting a variable from the context after execution
# print(f"Value of x in context: {context.get('private:x')}")
```
*Note: The exact structure of `result_info` and context interaction in the programmatic API example is illustrative and depends on the `REPL` class implementation.* 

## 4. Multiline Input and Block Handling

The REPL intelligently handles multiline input, which is essential for Dana's block-structured syntax (e.g., for `if`, `for`, `while`, `func` statements). The prompt typically changes (e.g., to `... `) for continuation lines.

**Mechanism**:
1.  User types a line of Dana code.
2.  The REPL internally attempts to parse the cumulative input so far.
3.  If the parser indicates the input is incomplete (e.g., an `if` statement expecting an indented block), the REPL prompts for more input.
4.  This continues until the parser deems a statement or block complete.
5.  A special sequence (e.g., `##` on a new line, or sometimes just dedenting) can signal the end of a multiline block if auto-detection is ambiguous or needs override.

**Example**:
```dana
dana> private:my_var = 15
dana> if private:my_var > 10:
...     log("Variable is greater than 10")
...     private:category = "high"
... else:
...     log("Variable is less than or equal to 10")
...     private:category = "low"
... 
# Execution happens after the final empty continuation or explicit end signal
```

## 5. Special Commands and NLP Mode

The REPL often includes special commands, usually prefixed (e.g., `##`), for meta-operations:

-   `##nlp on|off|status`: Manage Natural Language Processing mode.
-   `##clear_context`: Potentially a command to reset parts or all of the `SandboxContext`.
-   `##`: Force execution/completion of a multiline block.
-   `help` or `?`: Display help information.
-   `exit` or `quit`: Terminate the REPL session.

When NLP mode is active (and an LLM is available), non-command input might be first sent to a transcoder to convert it to Dana code before execution.

**NLP Mode Example**:
```dana
dana> ##nlp on
NLP mode enabled.
dana> create a variable named 'message' with the value 'Hello, Dana!'
# (Transcoded to: private:message = "Hello, Dana!")
dana> log(private:message)
# (Output: Hello, Dana!)
```

## 6. State Management (Scopes)

The REPL maintains a single `SandboxContext` throughout its session. This means variables set in one command are available in subsequent commands, respecting Dana's scoping rules (`local:`, `private:`, `public:`, `system:`). The `local:` scope typically refers to the immediate scope of the line or block being executed.

## 7. Error Handling

The REPL displays errors encountered during:
-   Parsing (syntax errors)
-   Interpretation (runtime errors, type issues if checks are performed)
-   LLM interaction (if NLP mode is used)

After an error, the REPL usually resets its input state, allowing the user to try again, while the `SandboxContext` generally persists.

## 8. LLM Integration for NLP

For NLP capabilities, the REPL system integrates with an LLM, typically configured via API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) or a configuration file (`opendxa_config.json`). This enables the transcoding of natural language queries into executable Dana code.

---
*Self-reflection: This document needs to be kept in sync with the actual CLI REPL (`dana_repl_app.py`) and the programmatic REPL (`repl.py`) as they evolve. Links to Parser and Transcoder design documents are important once those are finalized in the new structure.* 