"""Planning strategies."""

from enum import Enum

class PlanStrategy(Enum):
    """Planning strategies."""
    DEFAULT = "DEFAULT"        # Default strategy (implemented as direct execution)
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"  # Strategy for when workflow is treated as a plan
    DYNAMIC = "DYNAMIC"      # Adapt the plan during execution
    INCREMENTAL = "INCREMENTAL"  # Plan only a few steps ahead 