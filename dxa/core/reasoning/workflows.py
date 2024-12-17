"""Workflow definitions and handlers."""

from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class Workflow:
    """Workflow definition."""
    steps: List[Dict[str, Any]]
    transitions: Dict[str, str]
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Workflow":
        """Create workflow from YAML definition."""

class WorkflowEngine:
    """Workflow execution engine."""
    
    async def execute(self, workflow: Workflow, context: Any):
        """Execute workflow steps.""" 