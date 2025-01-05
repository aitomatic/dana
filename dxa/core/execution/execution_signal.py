"""Signal types for execution flow."""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional

class ExecutionSignalType(Enum):
    """Types of execution signals."""
    RESULT = "RESULT"
    ERROR = "ERROR"
    STATUS = "STATUS"

@dataclass
class ExecutionSignal:
    """Signal for execution flow control."""
    type: ExecutionSignalType
    content: Any
    metadata: Optional[dict] = None 