# DANA REPL (Read-Eval-Print Loop)

The DANA REPL provides an interactive environment for executing DANA code and natural language statements. It supports both single-line and multiline input, making it easier to write complex DANA programs interactively.

## Features

- Interactive execution of DANA code
- Natural language transcoding (when an LLM resource is configured)
- Command history with recall using arrow keys
- Keyword-based tab completion
- **Multiline input support for blocks and complex statements**

## Usage

To start the REPL, run:

```bash
python -m opendxa.dana.dana_repl
```

### Basic Commands

- Type DANA code or natural language at the `dana>` prompt
- Use `exit` or `quit` to exit the REPL
- Press Ctrl+C to cancel the current input
- Press Ctrl+D to exit the REPL

### Special Commands

- Type `##` on a new line to force execution of a multiline block, even if the parser thinks it's incomplete
- Use arrow keys to navigate command history
- Press Tab for keyword completion

### Multiline Input

The REPL supports multiline statements and blocks, which is especially useful for conditional statements, loops, and other complex code structures.

When entering multiline code:

1. Start typing your code at the `dana>` prompt
2. If your input is incomplete (e.g., an `if` statement without a body), the prompt will change to `.... ` to indicate continuation
3. Continue entering code lines until the statement or block is complete
4. Once the code is complete, it will be automatically executed

**Example: Multiline If Statement**

```
dana> if temp.x > 10:
....     log.info("Value is greater than 10")
....     temp.result = "high"
.... else:
....     log.info("Value is less than or equal to 10")
....     temp.result = "low"
```

The REPL detects incomplete input by:
- Checking for balanced brackets, parentheses, and braces
- Detecting block statements (like `if` and `while`) and ensuring they have bodies
- Examining assignments to ensure they have values
- Using the parser to check for completeness

### Memory Spaces

The REPL provides access to all standard DANA memory spaces:

- `private` - Private context for temporary variables within a program
- `agent` - Long-lived agent memory that persists between statements
- `world` - World state representing the external environment
- `temp` - Temporary workspace that persists during a REPL session
- `execution` - Current execution context (system variables)

### Special Statements

The REPL supports all DANA statements, including:

- Variable assignments
- `log` statements
- `print` statements
- `reason` statements
- Conditional statements (`if`/`else`)
- Loops (`while`)

## LLM Integration

When started with a configured LLM resource, the REPL enables:

1. **Natural language transcoding** - Convert natural language to DANA code
2. **Reasoning capabilities** - Use `reason()` statements to invoke LLM reasoning

To enable these features, set one of the supported API keys as an environment variable:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AZURE_OPENAI_API_KEY`
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`

Or configure models in `opendxa_config.json`.

## Tips for Multiline Input

1. Ensure proper indentation for block statements
2. For if-else statements, make sure each block has at least one statement
3. When entering a complex expression with parentheses, ensure they're balanced
4. To cancel a multiline input, press Ctrl+C

## Error Handling

The REPL provides error messages for:
- Syntax errors
- Type errors
- Runtime errors
- LLM-related errors (for reason statements)

After an error, the input state is reset, allowing you to start fresh.

## Working with Multiline Blocks

The REPL's multiline support follows Python-like indentation rules:

- Block statements (like `if`, `while`) must end with a colon (`:`)
- The body of a block must be indented (with spaces or tabs)
- The REPL will continue collecting input until the block structure is complete
- Dedent to the original level to complete a block

If you need to force execution of an incomplete block (for example, if the parser incorrectly thinks your input is incomplete), type `##` on a new line:

```
dana> if temp.x > 10:
....     log.info("High value")
.... ##
```

This will execute the input regardless of parser completeness checks.

## Examples

### Simple Variable Assignment

```
dana> temp.x = 42
```

### Multiline If Statement

```
dana> if temp.x > 100:
....     log.info("Value is very high")
.... elif temp.x > 50:
....     log.info("Value is high")
.... else:
....     log.info("Value is normal")
```

### While Loop

```
dana> temp.counter = 0
dana> while temp.counter < 5:
....     log.info("Counter: {temp.counter}")
....     temp.counter = temp.counter + 1
```

### Reason Statement

```
dana> temp.analysis = reason("What are the health implications of a temperature of {temp.value} degrees Celsius?")
dana> log.info("Analysis: {temp.analysis}")
```