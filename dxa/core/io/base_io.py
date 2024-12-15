"""Base I/O interface for DXA.

This module provides the abstract base class for all I/O implementations in DXA.
It defines the core interface that all I/O classes must implement to handle
input/output operations.

Example:
    ```python
    class CustomIO(BaseIO):
        async def send_message(self, message: str) -> None:
            # Implementation
            pass
            
        async def get_input(self, prompt: Optional[str] = None) -> str:
            # Implementation
            pass
    ```
"""

from abc import ABC
from typing import Optional
import logging
from dxa.agent.agent_runtime import StateManager

class BaseIO(ABC):
    """Base class for I/O implementations.
    
    This abstract class defines the interface for handling input/output operations
    in DXA. All I/O implementations must inherit from this class and implement
    its abstract methods.

    Attributes:
        logger: A logging instance for the I/O implementation.
        state_manager: A StateManager instance for tracking I/O state.
    """
    
    def __init__(self):
        """Initialize base I/O with logging and state management."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_manager = StateManager(self.__class__.__name__)
    
    async def send_message(self, message: str) -> None:
        """Send a message - must be implemented by subclasses."""
        pass
        
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input - must be implemented by subclasses."""
        pass

    async def initialize(self) -> None:
        """Default initialization does nothing."""
        pass

    async def cleanup(self) -> None:
        """Default cleanup does nothing."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 