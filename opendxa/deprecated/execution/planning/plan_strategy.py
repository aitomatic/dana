"""Planning strategies."""

from enum import Enum

class PlanStrategy(Enum):
    """Planning strategies."""
    DEFAULT = "DEFAULT"        # Default strategy (implemented as direct execution)
    DYNAMIC = "DYNAMIC"      # Adapt the plan during execution
    INCREMENTAL = "INCREMENTAL"  # Plan only a few steps ahead 