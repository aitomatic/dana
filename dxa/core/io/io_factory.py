"""
IO Factory
"""

from .base_io import BaseIO
from .console_io import ConsoleIO

class IOFactory:
    """Creates and configures IO systems."""
    
    @classmethod
    def create_io(cls) -> BaseIO:
        """Create basic ConsoleIO."""
        return ConsoleIO()
