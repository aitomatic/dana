"""
Resource Error Classes

Simple error classes for the new resource system.
"""


class ResourceError(Exception):
    """Exception raised for resource-related errors."""

    def __init__(self, message: str, resource_name: str = "", original_error: Exception = None):
        super().__init__(message)
        self.resource_name = resource_name
        self.original_error = original_error
