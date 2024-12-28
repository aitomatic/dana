"""Workflow implementation for high-level process."""

from typing import Optional
from ..execution import ExecutionGraph

class Workflow(ExecutionGraph):
    """High-level business process (WHY layer)."""
    
    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name, layer="workflow")