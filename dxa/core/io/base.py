"""Base I/O interface for DXA."""

from abc import ABC, abstractmethod
from typing import Optional
import logging
from dxa.core.state import StateManager

class BaseIO(ABC):
    """Base class for I/O implementations."""
    
    def __init__(self):
        """Initialize base I/O."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_manager = StateManager()
    
    @abstractmethod
    async def send_message(self, message: str) -> None:
        """Send a message."""
        pass
        
    @abstractmethod
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize I/O."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up I/O."""
        pass 