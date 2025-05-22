# AST Validation in Dana

## Introduction

When parsing code, it's important to ensure that the Abstract Syntax Tree (AST) is properly transformed from the initial parse tree. In the Dana parser, we use Lark for parsing, which produces an initial tree structure that is then transformed into a typed AST.

This document explains the AST validation system that helps ensure all Lark Tree nodes are properly transformed to Dana AST nodes.

## The Problem

The Dana parser uses Lark to parse program text into a parse tree, then transforms that parse tree into a structured AST using various transformer classes. Occasionally, transformer methods might miss handling certain node types, resulting in raw Lark Tree nodes remaining in the AST.

These untransformed nodes can cause problems:

1. **Type errors** - Downstream code expects Dana AST nodes, not Lark Tree nodes
2. **Inconsistent behavior** - Some AST operations work differently on Lark nodes vs. AST nodes
3. **Debugging challenges** - It can be hard to identify which transformer is responsible for the issue

## The Solution

We've implemented a comprehensive AST validation system that can:

1. **Detect** - Find any Lark Tree nodes that remain in the transformed AST
2. **Report** - Provide detailed path information about where these nodes are located
3. **Enforce** - Optionally enforce strict validation that raises exceptions for invalid ASTs

## Key Components

### Validation Functions

- **`find_tree_nodes(ast)`** - Recursively traverses an AST and returns a list of all Lark Tree nodes found, with their paths
- **`strip_lark_trees(ast)`** - Raises a TypeError when a Lark Tree node is found, showing the first problematic node
- **`safe_strip_lark_trees(ast)`** - A variant that avoids infinite recursion on cyclic ASTs

### StrictDanaParser

The `StrictDanaParser` class extends the standard `DanaParser` to enforce stricter AST validation:

```python
from opendxa.dana.sandbox.parser.strict_dana_parser import StrictDanaParser

# Create a parser that raises exceptions for invalid ASTs
parser = StrictDanaParser(strict_validation=True)

# Parse with validation
try:
    ast = parser.parse("your_code_here")
except TypeError as e:
    print(f"AST validation failed: {e}")
```

You can also use the factory function:

```python
from opendxa.dana.sandbox.parser.strict_dana_parser import create_parser

# Choose between regular or strict parser
parser = create_parser(strict=True)
```

### AstValidator Mixin

For advanced use cases, you can use the `AstValidator` mixin:

```python
from opendxa.dana.sandbox.parser.ast_validator import AstValidator

class MyCustomParser(SomeBaseParser, AstValidator):
    def parse(self, text):
        ast = super().parse(text)
        # Validate the AST
        is_valid, nodes = self.validate_ast(ast, strict=False)
        if not is_valid:
            print(f"Found {len(nodes)} Lark Tree nodes in the AST")
        return ast
```

## Best Practices

1. **During development**: Use the StrictDanaParser to catch transformer issues early
2. **In tests**: Add AST validation assertions to your test cases
3. **In production**: Consider using non-strict validation with warnings
4. **When fixing issues**: Use the path information to identify which transformer needs to be updated

## Contributing New Transformers

When creating new transformers for the Dana parser:

1. Make sure to handle all possible node types in your transformer methods
2. Always return a proper Dana AST node, never a Lark Tree node
3. Use the validation functions to check that your output contains no Tree nodes
4. Add tests that use StrictDanaParser to ensure your transformer works correctly

By following these practices, you'll help maintain a clean, well-structured AST that's easier to work with throughout the Dana system. 