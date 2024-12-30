"""Workflow implementation for high-level process."""

from typing import List, Dict, Any, Optional, Union
from ...common.graph import NodeType
from ..execution import ExecutionGraph, ExecutionSignal, Objective, ExecutionNode

class Workflow(ExecutionGraph):
    """High-level business process (WHY layer)."""

    def __init__(self, objective: Optional[Union[str, Objective]] = None, name: Optional[str] = None):
        super().__init__(objective, name=name)
        self._cursor = None
        self._set_minimal_workflow(objective)

    def _set_minimal_workflow(self, objective: Optional[Objective] = None):
        """Create workflow graph from objective."""
        # For simple QA, create linear workflow
        self.objective = objective

        # Add START node
        self.add_node(ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        
        # Add question task
        self.add_node(ExecutionNode(
            node_id="ANSWER_QUESTION",
            node_type=NodeType.TASK,
            description=str(objective)
        ))
        self.add_transition("START", "ANSWER_QUESTION")
        
        # Add END node
        self.add_node(ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        ))
        self.add_transition("ANSWER_QUESTION", "END")
        
    def update_from_signal(self, signal: ExecutionSignal) -> None:
        """Update workflow based on signal."""
        pass  # For simple QA, no updates needed

    def process_signal(self, signal: ExecutionSignal) -> List[ExecutionSignal]:
        """Process signal and generate new signals."""
        return []  # For simple QA, no new signals needed

    @classmethod
    def natural_language_to_yaml(cls, text: str) -> Dict[str, Any]:
        """Convert natural language to YAML format.
        For now, create a simple sequential workflow."""
        yaml_data = {
            "nodes": [
                {"id": "start", "type": "START", "description": "Begin workflow"},
                {"id": "task_1", "type": "TASK", "description": text},
                {"id": "end", "type": "END", "description": "End workflow"}
            ],
            "edges": [
                {"from": "start", "to": "task_1"},
                {"from": "task_1", "to": "end"}
            ]
        }
        return yaml_data

    def update_cursor(self, node_id: str) -> None:
        """Update workflow cursor to specified node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        self._cursor = self.get_a_cursor(self.nodes[node_id])