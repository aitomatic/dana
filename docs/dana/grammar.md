<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[◀ Parser](./parser.md) | [Transformers ▶︎](./transformers.md)

# DANA Grammar

**Files**:
    - `opendxa/dana/language/dana_grammar.lark`: The Lark grammar file.
    - `opendxa/dana/language/dana_grammar_embedded.py`: The back-up grammar file, in case Lark is not available for some reason.

The DANA Parser uses the Lark parser to parse the DANA source code into a parse tree.

This document describes the formal grammar definition for the DANA language, as implemented in the Lark grammar file. The grammar defines the syntax rules for parsing DANA source code into a parse tree, which is then transformed into an AST.

## Overview

The DANA grammar is written in [Lark](https://github.com/lark-parser/lark) EBNF syntax. It specifies the structure of valid DANA programs, including statements, expressions, literals, and control flow constructs. The grammar is designed to be readable, extensible, and to support indentation-based blocks.

## Main Rules

- **start**: Entry point for parsing; matches a complete DANA program.
- **program**: Sequence of statements.
- **statement**: Assignment, conditional, while loop, function call, print statement, bare identifier, or newline.
- **assignment**: Variable assignment (`x = expr`).
- **conditional**: If/else block with indented body.
- **while_loop**: While loop with indented body.
- **function_call**: Function or core function call.
- **print_statement**: Print statement.
- **bare_identifier**: Standalone identifier.
- **expression**: Supports logical, comparison, arithmetic, and unary operations.
- **literal**: String, number, boolean, or null.
- **identifier**: Variable or function name, with optional scope prefix.

## Grammar Structure Diagram

```mermaid
graph TD
    Start["start"] --> Program["program"]
    Program --> Statements
    subgraph Statements
        direction TB
        Assignment
        Conditional
        WhileLoop
        FunctionCall
        PrintStatement
        BareIdentifier
        ETC[...]
        Conditional --> Statement
        WhileLoop --> Statement
        Assignment --> Expression
        Conditional --> Expression
        WhileLoop --> Expression
        FunctionCall --> Expression
        PrintStatement --> Expression
        BareIdentifier --> Identifier
    end
    Statements --> Expressions
    subgraph Expressions
        direction TB
        Expression
        Identifier
        Literal
        ETC2[...]
        Expression --> Identifier
        Expression --> Literal
        Identifier --> ETC2
        Literal --> ETC2
    end
```

## Special Syntax and Features

- **Indentation**: Uses `INDENT` and `DEDENT` tokens for block structure (handled by the parser's indenter).
- **Comments**: Supports C-style (`/* ... */`) and C++-style (`// ...`) comments.
- **Scope Prefixes**: Identifiers can have prefixes like `private.`, `public.`, or `protected.`
- **Flexible Expressions**: Logical (`and`, `or`, `not`), comparison (`==`, `!=`, `<`, `>`, etc.), arithmetic (`+`, `-`, `*`, `/`, `%`), and function calls.
- **Literals**: Strings, numbers, booleans, and null values.

## Extensibility

The grammar is designed to be extensible. New statements, expressions, or literal types can be added by extending the grammar file and updating the parser and transformers accordingly.

## Example: Minimal DANA Program

```dana
x = 42
if x > 10:
    print("large")
else:
    print("small")
```

## Mapping the Example Program to Grammar and AST

### Grammar Rule Mapping

| Code                        | Grammar Rule(s) Triggered                |
|-----------------------------|------------------------------------------|
| `x = 42`                    | statement → assignment                   |
|                             | assignment → identifier '=' expression   |
| `if x > 10:`                | statement → conditional                  |
|                             | conditional → 'if' expression ':' ...    |
| `    print("large")`        | statement → function_call                |
|                             | function_call → identifier '(' ... ')'   |
| `else:`                     | conditional (else branch)                |
| `    print("small")`        | statement → function_call                |

### Simplified Parse Tree

```
program
 ├─ assignment
 │   ├─ identifier: x
 │   └─ expression: 42
 └─ conditional
     ├─ expression: x > 10
     ├─ statement: function_call (print("large"))
     └─ else statement: function_call (print("small"))
```

### Corresponding AST

```mermaid
graph TD
    Program[Program]
    Assignment[Assignment: x = 42]
    Conditional[Conditional: if x > 10]
    Identifier[Identifier: x]
    Literal42[Literal: 42]
    BinaryExpr[BinaryExpression: x > 10]
    Identifier2[Identifier: x]
    Literal10[Literal: 10]
    Print1[FunctionCall: print]
    LiteralLarge[Literal: 'large']
    Print2[FunctionCall: print]
    LiteralSmall[Literal: 'small']

    Program --> Assignment
    Program --> Conditional
    Assignment --> Identifier
    Assignment --> Literal42
    Conditional --> BinaryExpr
    BinaryExpr --> Identifier2
    BinaryExpr --> Literal10
    Conditional --> Print1
    Print1 --> LiteralLarge
    Conditional --> Print2
    Print2 --> LiteralSmall
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 