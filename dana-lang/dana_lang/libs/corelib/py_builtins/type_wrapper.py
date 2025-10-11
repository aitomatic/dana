"""
Secure type wrapper for Dana's sandbox environment.

This module provides a wrapper type object that gives rich type information
while maintaining security boundaries and preventing introspection attacks.
"""

from typing import Any


class DanaTypeWrapper:
    """Secure wrapper for type information that prevents introspection attacks.

    This wrapper provides rich type information while maintaining security
    boundaries. It exposes only safe information and prevents access to
    internal Python type system details.
    """

    def __init__(self, obj: Any, type_name: str, is_constructor: bool = False):
        """Initialize the type wrapper.

        Args:
            obj: The object being wrapped
            type_name: The type name as a string
            is_constructor: Whether this is a constructor function
        """
        self._obj = obj
        self._type_name = type_name
        self._is_constructor = is_constructor

        # Extract additional safe information
        self._extract_safe_info()

    def _extract_safe_info(self):
        """Extract safe type information without exposing internals."""
        # For instances, try to get the underlying type name
        if hasattr(self._obj, "_type") and hasattr(self._obj._type, "name"):
            self._underlying_type_name = self._obj._type.name
        else:
            self._underlying_type_name = None

        # Determine if this is a resource, agent, or struct instance
        if hasattr(self._obj, "start"):  # ResourceInstance has start() method
            self._instance_type = "Resource"
        elif hasattr(self._obj, "plan") and hasattr(self._obj, "solve") and hasattr(self._obj, "chat"):  # AgentInstance has agent methods
            self._instance_type = "Agent"
        elif hasattr(self._obj, "_type") and hasattr(self._obj._type, "fields"):
            self._instance_type = "Struct"
        else:
            self._instance_type = None

    def __str__(self) -> str:
        """Return a string representation of the type."""
        if self._is_constructor:
            if self._type_name == "function":
                # Try to determine if it's a resource or struct constructor
                if hasattr(self._obj, "__name__"):
                    return f"Constructor[{self._obj.__name__}]"
                else:
                    return "Constructor"
            else:
                return self._type_name

        # For instances, provide more informative type information
        if self._instance_type and self._underlying_type_name:
            return f"{self._instance_type}[{self._underlying_type_name}]"
        else:
            return self._type_name

    def __repr__(self) -> str:
        """Return a detailed representation of the type."""
        return self.__str__()

    @property
    def name(self) -> str:
        """Get the type name."""
        return self._type_name

    @property
    def is_constructor(self) -> bool:
        """Check if this is a constructor function."""
        return self._is_constructor

    @property
    def is_instance(self) -> bool:
        """Check if this is an instance."""
        return not self._is_constructor

    @property
    def instance_type(self) -> str | None:
        """
        Get the instance type of the wrapped object.

        Returns:
            str: The type of instance, such as "ResourceInstance" or "StructInstance".
            None: If the object is not recognized as a resource or struct instance.
        """
        return self._instance_type

    @property
    def underlying_type_name(self) -> str | None:
        """
        Get the underlying type name for instances.

        Returns:
            str: The name of the underlying type if available (e.g., the resource or struct type name).
            None: If the underlying type name cannot be determined or is not applicable.
        """
        return self._underlying_type_name

    def __eq__(self, other) -> bool:
        """Compare type wrappers for equality."""
        if isinstance(other, DanaTypeWrapper):
            return (
                self._type_name == other._type_name
                and self._is_constructor == other._is_constructor
                and self._instance_type == other._instance_type
                and self._underlying_type_name == other._underlying_type_name
            )
        elif isinstance(other, str):
            return str(self) == other
        else:
            return False

    def __hash__(self) -> int:
        """Hash the type wrapper."""
        return hash((self._type_name, self._is_constructor, self._instance_type, self._underlying_type_name))


def create_type_wrapper(obj: Any) -> DanaTypeWrapper:
    """Create a secure type wrapper for an object.

    Args:
        obj: The object to create a type wrapper for

    Returns:
        DanaTypeWrapper with safe type information
    """
    # Get the basic type name
    type_name = type(obj).__name__

    # Determine if this is a constructor function
    is_constructor = callable(obj) and not hasattr(obj, "_type")

    return DanaTypeWrapper(obj, type_name, is_constructor)
