from typing import TYPE_CHECKING, Optional

from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

if TYPE_CHECKING:
    from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter


class HasInterpreter:
    """Mixin for classes that have an interpreter."""

    def __init__(self, interpreter: Optional["DanaInterpreter"] = None):
        self._interpreter: Optional[DanaInterpreter] = interpreter

    @property
    def interpreter(self) -> "DanaInterpreter":
        """Get the interpreter instance."""
        if self._interpreter is None:
            raise RuntimeError("Interpreter not set")
        return self._interpreter

    @interpreter.setter
    def interpreter(self, interpreter: "DanaInterpreter"):
        """Set the interpreter instance.

        This is called by the interpreter after instantiation to establish
        the link between the executor and its parent interpreter.

        Args:
            interpreter: The interpreter instance
        """
        self._interpreter = interpreter

    def get_interpreter(self) -> Optional["DanaInterpreter"]:
        """Get the interpreter instance or None if not set.

        Unlike the property, this method returns None instead of raising an exception
        if the interpreter is not set.

        Returns:
            The interpreter instance or None
        """
        return self._interpreter

    @property
    def function_registry(self) -> FunctionRegistry:
        """Get the function registry from the interpreter."""
        if self.interpreter is None:
            raise RuntimeError("Interpreter not set")
        return self.interpreter.function_registry
