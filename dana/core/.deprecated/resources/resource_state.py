"""
Resource State Enum

Defines resource lifecycle states.
"""

from enum import Enum


class ResourceState(Enum):
    """Resource lifecycle states."""

    DEFINED = "defined"  # Resource type defined, not instantiated
    CREATED = "created"  # Resource instance created, not initialized
    RUNNING = "running"  # Resource active and available
    SUSPENDED = "suspended"  # Resource temporarily unavailable
    TERMINATED = "terminated"  # Resource permanently shut down
