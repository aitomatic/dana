"""
Sandbox Interface Protocol for Python-to-Dana Integration

Defines the common interface protocol that all sandbox implementations must follow.
This enables clean separation between different execution models (in-process, subprocess, etc.)
while maintaining a consistent API.
"""

from typing import Any, Protocol


class SandboxInterface(Protocol):
    """Protocol interface for Dana sandbox implementations.

    This protocol defines the common interface that all sandbox implementations
    must implement, whether they run in-process, in a subprocess, or in any
    other execution environment.
    """

    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Execute Dana reasoning function.

        Args:
            prompt: The question or prompt to send to the LLM
            options: Optional parameters for LLM configuration

        Returns:
            The LLM's response to the prompt

        Raises:
            DanaCallError: If the Dana reasoning call fails
        """
        ...

    def execute_function(self, func_name: str, args: tuple = (), kwargs: dict | None = None) -> Any:
        """Execute a Dana function with given arguments.

        Args:
            func_name: Name of the Dana function to execute
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the Dana function execution

        Raises:
            DanaCallError: If the Dana function call fails
        """
        ...

    def exec_module(self, file_path: str) -> Any:
        """Execute a Dana module from a file path.

        Args:
            file_path: Path to the Dana (.na) file to execute

        Returns:
            The execution result containing context and any return values

        Raises:
            DanaCallError: If the Dana module execution fails
        """
        ...

    def close(self) -> None:
        """Close the sandbox and cleanup resources.

        Implementations should ensure proper cleanup of any resources
        (processes, connections, etc.) when this method is called.
        """
        ...
