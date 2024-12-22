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

from typing import Optional, Any
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
    
    async def send(self, message: Any) -> None:
        """Print to console."""
        print(message)

    async def receive(self) -> Any:
        """Get input from console."""
        return input("> ")

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