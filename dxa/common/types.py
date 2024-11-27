"""Common type definitions used across the DXA system.

This module defines fundamental type aliases and custom types that are used
throughout the DXA codebase. These types provide consistent type hints for:
- JSON-compatible data structures
- Common data interchange formats
- System-wide data structures

The types defined here should be used instead of raw type annotations to ensure
consistency and maintainability.
"""

from typing import Dict, Union, List

# Basic JSON-compatible types
JsonPrimitive = Union[str, int, float, bool, None]
JsonType = Union[JsonPrimitive, List['JsonType'], Dict[str, 'JsonType']]

# Add any other common type definitions here as needed 