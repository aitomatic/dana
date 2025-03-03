"""Workflow implementation for high-level process."""

from typing import List, Dict, Any, Optional, Union

from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionSignal, Objective

class Workflow(ExecutionGraph):
    """High-level business process (WHY layer)."""

    def __init__(self, objective: Optional[Union[str, Objective]] = None, name: Optional[str] = None):
        super().__init__(objective, name=name)
        self._cursor = None
        self._objective = objective if isinstance(objective, Objective) else Objective(objective)

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

    def pretty_print(self) -> str:
        """Generate a human-readable representation of the workflow.
        
        Returns:
            A formatted string representation of the workflow
        """
        output = []
        
        # Basic workflow information
        output.append(f"Workflow Name: {self.name}")
        if self.objective:
            output.append(f"Objective: {self.objective.original}")
        output.append(f"Agent Role: {self.metadata.get('role', 'No role specified')}")
        output.append(f"Number of nodes: {len(self.nodes)}")
        output.append(f"Number of edges: {len(self.edges)}")
        
        # Print detailed node information
        output.append("\nWorkflow Nodes:")
        for node_id, node in self.nodes.items():
            output.append(f"\nNode ID: {node_id}")
            output.append(f"  Type: {node.node_type.name}")
            
            # Print node description (truncated if too long)
            if len(node.description) > 50:
                output.append(f"  Description: {node.description[:50]}...")
            else:
                output.append(f"  Description: {node.description}")
            
            # Print node metadata with special handling for certain fields
            if node.metadata:
                output.append("  Metadata:")
                # First print prompt for emphasis
                if 'prompt' in node.metadata:
                    prompt = node.get_prompt()
                    output.append(f"    prompt: {prompt}")
                
                # Then print planning and reasoning
                if 'planning' in node.metadata:
                    output.append(f"    planning: {node.metadata['planning']}")
                if 'reasoning' in node.metadata:
                    output.append(f"    reasoning: {node.metadata['reasoning']}")
                
                # Then print any other metadata
                for key, value in node.metadata.items():
                    if key not in ['planning', 'reasoning', 'prompt']:  # Skip already printed items
                        if isinstance(value, str) and len(value) > 50:
                            output.append(f"    {key}: {value[:50]}...")
                        else:
                            output.append(f"    {key}: {value}")
        
        # Print edge details
        output.append("\nWorkflow Edges:")
        for edge in self.edges:
            output.append(f"  {edge.source} -> {edge.target}")
            if edge.metadata:
                output.append(f"    Conditions: {edge.metadata.get('condition', 'None')}")
        
        return "\n".join(output)