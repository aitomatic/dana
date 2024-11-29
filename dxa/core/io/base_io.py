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

from abc import ABC, abstractmethod
from typing import Optional
import logging
from dxa.agent.agent_state import StateManager

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
    
    @abstractmethod
    async def send_message(self, message: str) -> None:
        """Send a message through the I/O implementation.
        
        Args:
            message: The message string to be sent.
            
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        pass
        
    @abstractmethod
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input through the I/O implementation.
        
        Args:
            prompt: Optional prompt to display before getting input.
            
        Returns:
            str: The input received from the I/O implementation.
            
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize I/O."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up I/O."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 