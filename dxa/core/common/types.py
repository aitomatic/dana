"""Common type definitions used across the system."""

from typing import Dict, Union, List

# Basic JSON-compatible types
JsonPrimitive = Union[str, int, float, bool, None]
JsonType = Union[JsonPrimitive, List['JsonType'], Dict[str, 'JsonType']]

# Add any other common type definitions here as needed 