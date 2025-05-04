"""Common type definitions used across the DXA system.

This module defines fundamental type aliases and custom types that are used
throughout the DXA codebase. These types provide consistent type hints for:
- JSON-compatible data structures
- Common data interchange formats
- System-wide data structures

The types defined here should be used instead of raw type annotations to ensure
consistency and maintainability.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

# Basic JSON-compatible types
JsonPrimitive = Union[str, int, float, bool, None]
JsonType = Union[JsonPrimitive, List["JsonType"], Dict[str, "JsonType"]]

# Add any other common type definitions here as needed


class BaseRequest(BaseModel):
    """Base class for all request types.

    This serves as a base class for all request types in the system.
    Subclasses should add their specific fields while inheriting the base structure.

    Attributes:
        arguments: Arguments/parameters for the request
    """

    arguments: Dict[str, Any] = {}


class BaseResponse(BaseModel):
    """Base class for all response types.

    This serves as a base class for all response types in the system.
    Subclasses should add their specific fields while inheriting the base structure.

    Attributes:
        success: Whether the operation was successful
        error: Error message if the operation failed
        content: The response content
    """

    success: bool
    error: Optional[str] = None
    content: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary.

        Returns:
            A dictionary representation of the response.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """Convert the response to a JSON string.

        Returns:
            A JSON string representation of the response.
        """
        return self.model_dump_json()
