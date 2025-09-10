"""
Resource State Enum

Defines the possible states of a resource instance.
"""

from enum import Enum


class ResourceState(Enum):
    """Resource lifecycle states."""

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"
