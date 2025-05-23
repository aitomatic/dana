# Dana REPL Multiline Examples

This file contains examples of using the Dana REPL with multiline statements and blocks.

**New in this version:** The REPL now uses explicit ending for multiline blocks. Press Enter on an empty line to execute multiline code.

## Variable Assignment

```
dana> temp.x = 42
dana> log.info("Value of x: {temp.x}")
```

## If-Else Statement (New Explicit Multiline)

```
dana> if temp.x > 50:
...     log.info("Value is high")
...     temp.result = "high"
... else:
...     log.info("Value is low")
...     temp.result = "low"
... [empty line - executes the block]
dana> log.info("Result: {temp.result}")
```

## While Loop

```
dana> temp.counter = 0
dana> while temp.counter < 5:
...     log.info("Counter: {temp.counter}")
...     temp.counter = temp.counter + 1
... [empty line - executes the block]
dana> log.info("Final counter value: {temp.counter}")
```

## Forced Multiline Mode

You can also force multiline mode with `##`:

```
dana> ##
✅ Forced multiline mode - type your code, end with empty line
... temp.x = 25
... temp.y = 15
... if temp.x > 20:
...     log.info("X is greater than 20")
...     if temp.y > 10:
...         log.info("Both X and Y are high")
...     else:
...         log.info("Only X is high")
... [empty line - executes the block]
```

## Benefits of Explicit Ending

This new approach solves several issues:

1. **If-else continuity**: You can now write complete if-else blocks without the REPL executing prematurely
2. **Predictable behavior**: The REPL only executes when you explicitly end with an empty line
3. **Flexibility**: You can build complex multiline constructs incrementally

## Old Behavior vs New Behavior

### Old (problematic):
```
dana> if local.a == 365:
...     print(a/10)      [executes here - problematic!]
dana> else:              [orphaned else statement]
...     print(1)
```

### New (correct):
```
dana> if local.a == 365:
...     print(a/10)
... else:
...     print(1)
... [empty line - executes complete if-else block]
```

## Nested Blocks

```
dana> temp.x = 25
dana> temp.y = 15
dana> if temp.x > 20:
...     log.info("X is greater than 20")
...     if temp.y > 10:
...         log.info("Both X and Y are high")
...     else:
...         log.info("Only X is high")
...
dana> log.info("Done evaluating conditions")
```

## Using Force Execute (##)

If the parser incorrectly thinks your input is incomplete, you can force execution:

```
dana> if temp.value > 100:
...     log.info("High temperature")
... ##
```

This is useful when:
- The parser incorrectly detects an incomplete statement
- You want to execute partial code for testing
- You're debugging complex blocks

## Handling Errors

If there's an error in your multiline code, the REPL will display the error and reset:

```
dana> if temp.value > 100:
...     log.info("Temperature: {temp.valu}")  # Typo in variable name
...
Error: Undefined variable temp.valu in f-string
```

## Reason Statement in Multiline Context

```
dana> temp.temperature = 39.5
dana> if temp.temperature > 38.0:
...     temp.analysis = reason("What are the health implications of a temperature of {temp.temperature} degrees Celsius?")
...     log.info("Analysis: {temp.analysis}")
... else:
...     log.info("Temperature is normal")
...
```

## Canceling Input

You can cancel multiline input at any time with Ctrl+C:

```
dana> if temp.x > 100:
...     log.info("Value is very high")
...     ^C
Input cancelled.
```
