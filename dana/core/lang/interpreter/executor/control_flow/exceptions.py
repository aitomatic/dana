"""
Control flow exceptions for Dana language.

This module defines the special exceptions used for control flow
in the Dana language interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""


# Special exceptions for control flow
class BreakException(Exception):
    """Exception to handle break statements."""

    pass


class ContinueException(Exception):
    """Exception to handle continue statements."""

    pass


class ReturnException(Exception):
    """Exception to handle return statements."""

    def __init__(self, value=None):
        """Initialize the return exception with a return value.

        Args:
            value: The value to return
        """
        self.value = value
        # Don't convert value to string to avoid triggering promise resolution
        super().__init__(f"Return with value: {type(value).__name__}")


class DeliverException(Exception):
    """Exception to handle deliver statements (eager execution)."""

    def __init__(self, value=None):
        """Initialize the deliver exception with a deliver value.

        Args:
            value: The value to deliver
        """
        self.value = value
        # Don't convert value to string to avoid triggering promise resolution
        super().__init__(f"Deliver with value: {type(value).__name__}")
