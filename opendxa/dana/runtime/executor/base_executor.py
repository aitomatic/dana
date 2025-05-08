"""Base executor for the DANA interpreter.

This module provides the base executor class that defines the interface
for all DANA execution components.
"""

import uuid

from opendxa.common.mixins.loggable import Loggable


class BaseExecutor(Loggable):
    """Base class for DANA execution components.

    This class provides common functionality used across all execution components:
    - Logging utilities
    - Execution ID management
    - Error handling hooks
    """

    def __init__(self):
        """Initialize the base executor."""
        # Initialize Loggable with prefix for all DANA logs
        super().__init__(prefix="dana")

        # Generate execution ID for this run
        self._execution_id = str(uuid.uuid4())[:8]  # Short unique ID for this execution
