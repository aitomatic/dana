from typing import TYPE_CHECKING, Optional

from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

if TYPE_CHECKING:
    from opendxa.dana.sandbox.interpreter.interpreter import Interpreter


class HasInterpreter:
    """Mixin for classes that have an interpreter."""

    def __init__(self, interpreter: Optional["Interpreter"] = None):
        self._interpreter: Optional[Interpreter] = interpreter

    @property
    def interpreter(self) -> "Interpreter":
        """Get the interpreter instance."""
        if self._interpreter is None:
            raise RuntimeError("Interpreter not set")
        return self._interpreter

    @interpreter.setter
    def interpreter(self, interpreter: "Interpreter"):
        """Set the interpreter instance.

        This is called by the interpreter after instantiation to establish
        the link between the executor and its parent interpreter.

        Args:
            interpreter: The interpreter instance
        """
        self._interpreter = interpreter

    @property
    def function_registry(self) -> FunctionRegistry:
        """Get the function registry from the interpreter."""
        if self.interpreter is None:
            raise RuntimeError("Interpreter not set")
        return self.interpreter.function_registry
