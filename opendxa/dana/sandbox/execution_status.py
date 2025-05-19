"""
Execution status enum for DANA sandbox.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from enum import Enum


class ExecutionStatus(Enum):
    """Execution status enum."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
