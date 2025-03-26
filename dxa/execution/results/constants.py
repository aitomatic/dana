"""Constants and types for execution results."""

from enum import Enum
from typing import Dict, Any, Optional

# OODA steps in order
OODA_STEPS = ['OBSERVE', 'ORIENT', 'DECIDE', 'ACT']

# Maximum number of recent results to keep
MAX_RECENT_RESULTS = 5

# Default token budget for context
DEFAULT_TOKEN_BUDGET = 2000

# Token budget allocation
RECENT_CONTEXT_RATIO = 0.7
HISTORICAL_CONTEXT_RATIO = 0.3

# Result types
class ResultType(Enum):
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    DECISION = "decision"
    ACTION = "action"

# Type aliases
ResultDict = Dict[str, Any]
ContextDict = Dict[str, ResultDict] 