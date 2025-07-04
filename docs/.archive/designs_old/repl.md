**Files**:
    - `opendxa.dana.exec.repl.repl`: The main REPL class (programmatic API)
    - `opendxa.dana.exec.repl.dana_repl_app`: The user-facing CLI application

# Dana REPL (Read-Eval-Print Loop)

The Dana REPL provides an interactive environment for executing Dana code and natural language statements. It supports both single-line and multiline input, making it easier to write complex Dana programs interactively.

The REPL uses the Parser to parse a Dana program into an AST, then calls the Interpreter to execute it. Context is managed using `SandboxContext`.

## Features

- Interactive execution of Dana code
- Natural language transcoding (when an LLM resource is configured)
- Command history with recall using arrow keys
- Keyword-based tab completion (via prompt_toolkit)
- Multiline input support for blocks and complex statements
- Special commands for NLP mode and REPL control

## Usage

To start the REPL CLI, run:

```bash
python -m dana.dana.exec.repl.dana_repl_app
```

Or use the programmatic API:

```python
from opendxa.dana.exec.repl.repl import REPL
repl = REPL()
result = repl.execute("x = 42\nprint(x)")
print(result)
```

## Multiline Input and Block Handling

The REPL supports multiline statements and blocks, which is especially useful for conditional statements, loops, and other complex code structures. The prompt changes to `...` for continuation lines.

**How it works:**
1. Start typing your code at the `dana>` prompt.
2. If your input is incomplete (e.g., an `if` statement without a body), the prompt will change to `...` to indicate continuation.
3. Continue entering code lines until the statement or block is complete.
4. Once the code is complete, it will be automatically executed.
5. To force execution of an incomplete block (if the parser thinks it's incomplete), type `##` on a new line.

**Example:**
```
dana> if private:x > 10:
...     print("Value is greater than 10")
...     private:result = "high"
... else:
...     print("Value is less than or equal to 10")
...     private:result = "low"
```

**Block rules:**
- Block statements (like `if`, `while`) must end with a colon (`:`)
- The body of a block must be indented (with spaces or tabs)
- The REPL will continue collecting input until the block structure is complete
- Dedent to the original level to complete a block

The REPL detects incomplete input by:
- Checking for balanced brackets, parentheses, and braces
- Detecting block statements and ensuring they have bodies
- Examining assignments to ensure they have values
- Using the parser to check for completeness

## Special Commands and NLP Mode

The REPL supports special commands (prefixed with `##`) for controlling NLP mode and other features:

- `##nlp on` — Enable natural language processing mode
- `##nlp off` — Disable NLP mode
- `##nlp status` — Show NLP mode status and LLM resource availability
- `##nlp test` — Test the NLP transcoder with common examples
- `##` (on a new line) — Force execution of a multiline block
- `help`, `?` — Show help
- `exit`, `quit` — Exit the REPL

When NLP mode is enabled and an LLM resource is configured, you can enter natural language and have it transcoded to Dana code.

**Example: Using NLP Mode**
```
dana> ##nlp on
✅ NLP mode enabled
dana> add 42 and 17
✅ Execution result:
59
```

## Memory Spaces

The REPL provides access to all standard Dana memory spaces:

- `private` — Private context for temporary variables within a program
- `public` — Shared public memory
- `system` — System variables and execution state
- `local` — Local scope for the current execution

## Error Handling

The REPL provides error messages for:
- Syntax errors
- Type errors
- Runtime errors
- LLM-related errors (for NLP mode)

After an error, the input state is reset, allowing you to start fresh.

## LLM Integration

When started with a configured LLM resource, the REPL enables:
- **Natural language transcoding** — Convert natural language to Dana code

To enable these features, set one of the supported API keys as an environment variable:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AZURE_OPENAI_API_KEY`
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`

Or configure models in `dana_config.json`.

## Tips

- Ensure proper indentation for block statements
- For if-else statements, make sure each block has at least one statement
- When entering a complex expression with parentheses, ensure they're balanced
- To cancel a multiline input, press Ctrl+C

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 
