"""Console I/O implementation for DXA.

This module provides a console-based implementation of the BaseIO interface,
allowing interaction through standard input/output streams.

Example:
    ```python
    async with ConsoleIO() as console:
        await console.send_message("Hello, world!")
        user_input = await console.get_input("Enter something: ")
    ```
"""

from typing import Optional
from dxa.core.io.base_io import BaseIO

class ConsoleIO(BaseIO):
    """Console-based I/O implementation.
    
    This class implements the BaseIO interface for console-based interaction,
    using standard input/output streams.

    Attributes:
        _buffer (list[str]): A list storing sent messages for testing purposes.
    """
    
    def __init__(self):
        super().__init__()  # Call the __init__ method of the base class
        self._buffer: list[str] = []  # For testing purposes
    
    async def send_message(self, message: str) -> None:
        """Send a message to console."""
        try:
            print(message)
            self._buffer.append(message)  # Store for testing
        except IOError as e:
            # Log error if you have logging configured
            raise IOError(f"Failed to write to console: {e}") from e
    
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input from console."""
        try:
            if prompt:
                print(prompt, end='')
            return input()
        except EOFError:
            return ''

    async def initialize(self) -> None:
        """Initialize console I/O."""
        self.state_manager.add_observation(
            content="Console I/O initialized",
            source="console_io"
        )

    async def cleanup(self) -> None:
        """Clean up console I/O."""
        self.state_manager.add_observation(
            content="Console I/O cleaned up",
            source="console_io"
        ) 