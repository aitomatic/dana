"""Console I/O implementation."""

from typing import Optional
from dxa.core.io.base import BaseIO

class ConsoleIO(BaseIO):
    """Console-based I/O implementation."""
    
    async def send_message(self, message: str) -> None:
        """Send a message to console."""
        print(f"\n{message}")
        # Track outgoing message
        self.state_manager.add_message(
            content=message,
            sender="system",
            receiver="user"
        )
        
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input from console."""
        if prompt:
            print(prompt)
        response = input("> ").strip()
        # Track user input
        self.state_manager.add_message(
            content=response,
            sender="user",
            receiver="system"
        )
        return response

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