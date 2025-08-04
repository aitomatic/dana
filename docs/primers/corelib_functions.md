# Dana Corelib Functions

Core functions preloaded at startup and automatically available in all Dana programs.

## Math Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sum_range(start, end)` | Sum numbers from start to end (inclusive) | `sum_range(1, 10)` → `55` |
| `is_odd(number)` | Check if number is odd | `is_odd(7)` → `True` |
| `is_even(number)` | Check if number is even | `is_even(8)` → `True` |
| `factorial(n)` | Calculate factorial | `factorial(5)` → `120` |

## Text Functions

| Function | Description | Example |
|----------|-------------|---------|
| `capitalize_words(text)` | Capitalize each word | `capitalize_words("hello world")` → `"Hello World"` |
| `title_case(text)` | Convert to title case | `title_case("dana language")` → `"Dana Language"` |

## AI/LLM Functions

| Function | Description | Example |
|----------|-------------|---------|
| `reason(prompt)` | AI reasoning and analysis | `reason("What is 2+2?")` |
| `llm(prompt, model)` | Direct LLM interactions | `llm("Hello", "gpt-4")` |
| `set_model(model)` | Set default LLM model | `set_model("claude-3")` |
| `context_aware_reason(prompt)` | Context-aware reasoning | `context_aware_reason("Analyze this")` |

## Logging & Output

| Function | Description | Example |
|----------|-------------|---------|
| `log(message)` | Log message | `log("Hello world")` |
| `print(value)` | Console output | `print("Hello")` |
| `log_level(level)` | Set log level | `log_level("DEBUG")` |

## Agent Functions

| Function | Description | Example |
|----------|-------------|---------|
| `agent(config)` | Create/configure agent | `agent({"name": "helper"})` |

## Utility Functions

| Function | Description | Example |
|----------|-------------|---------|
| `str(value)` | String conversion | `str(42)` → `"42"` |
| `cast(value, type)` | Type casting | `cast("123", "int")` |
| `use(module)` | Import module | `use("math")` |
| `noop()` | No operation | `noop()` |

## Framework Functions

| Function | Description | Example |
|----------|-------------|---------|
| `poet(func, args)` | POET enhancement | `poet("reason", ["Analyze"])` |
| `feedback(message)` | User feedback | `feedback("How was that?")` |

## Usage

```dana
# All functions are automatically available - no imports needed
result = sum_range(1, 100)
if is_even(result):
    log("Sum is even")

answer = reason("What is the capital of France?")
print(f"Answer: {answer}")

my_agent = agent({"role": "assistant"})
```

## Function Priority

1. User-defined functions
2. **Corelib functions** (preloaded)
3. Pythonic built-ins

**Total: 20 functions** across math, text, AI/LLM, logging, agents, utilities, and frameworks 