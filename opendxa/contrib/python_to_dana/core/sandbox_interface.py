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

    def close(self) -> None:
        """Close the sandbox and cleanup resources.

        Implementations should ensure proper cleanup of any resources
        (processes, connections, etc.) when this method is called.
        """
        ...
