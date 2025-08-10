# Comment Metadata

## Overview

Dana supports universal end-of-line comments with automatic metadata extraction for tooling and documentation.

## Comment Types

### Regular Comments (`#`)
Comments that are ignored by the parser and invisible to program execution:

```dana
x = 5  # This is a regular comment
data = [1, 2, 3]  # Comments work everywhere
```

### Metadata Comments (`##`)
Comments that are extracted and attached to AST nodes as metadata:

```dana
x = 5  ## Variable metadata
def process(data: list) -> str:  ## Function metadata
    return "processed"  ## Return value metadata
```

## Where Comments Work

Comments are supported in all contexts:

```dana
# Variable assignments
result = calculate(x, y)  # Regular comment

# Collections
numbers = [
    1,  # First item
    2,  ## Second item metadata
    3   # Third item
]

# Dictionary entries
config = {
    "host": "localhost",  # Server configuration
    "port": 8080,         ## Port metadata
    "debug": True         # Debug flag
}

# Function definitions
def add(a: int, b: int) -> int:  ## Addition function
    return a + b  # Simple addition

# Struct fields
struct Point:
    x: int  ## X coordinate metadata
    y: int  # Y coordinate comment

# Import statements
import math_utils  # Math utilities
```

## Accessing Metadata

Metadata comments are attached to AST nodes during parsing:

```python
# Parser extracts metadata and attaches to AST nodes
node.metadata['comment']  # Contains the ## comment text
```

## Key Features

- **Universal**: Comments work in all language constructs
- **Transparent**: Regular comments are invisible to program execution
- **Clean Collections**: `[1, 2, 3]` not `[1, Token('COMMENT'), 2, 3]`
- **Metadata Extraction**: `##` comments available for tooling
- **Backward Compatible**: Existing comment handling preserved

## Use Cases

- **Documentation**: Inline documentation for structs and functions
- **Tooling**: IDE support, linters, documentation generators
- **Annotations**: Type hints, deprecation notices, usage examples
- **Development**: Temporary notes that don't affect execution