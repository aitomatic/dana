"""Base workflow implementation using directed graphs."""

from pathlib import Path
from typing import Union, TextIO, cast
from ..execution_graph import ExecutionGraph

class Workflow(ExecutionGraph):
    """Workflow class for workflow patterns.
    
    A workflow is a directed graph where:
    - Nodes represent tasks, decisions, or control points
    - Edges represent valid transitions with conditions
    - The structure defines all possible execution paths
    - State changes are tracked through transitions
    """

    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'Workflow':
        """Create workflow from YAML specification."""
        return cast(Workflow, ExecutionGraph._from_yaml(stream, Workflow))
